import os
import re

from collections import defaultdict
from fnmatch import fnmatch
from time import sleep

from porkchop.plugin import PorkchopPlugin


class Filter(object):
    def __init__(self, filter):
        self.filter = filter

    def match(self, on):
        return self._filter(on)

    def _filter(self, on):
        raise NotImplementedError()

    @staticmethod
    def is_compatible(filter_string):
        raise NotImplementedError()


class PIDFileFilter(Filter):
    def __init__(self, *args, **kwargs):
        self.last_mtime = 0
        return super(PIDFileFilter, self).__init__(*args, **kwargs)

    @staticmethod
    def is_compatible(filter_string):
        return isinstance(filter_string, basestring) and os.access(filter_string, os.R_OK)

    def _filter(self, on):
        return on.split(os.sep)[2] in self.pids

    @property
    def pids(self):
        try:
            st_mtime = os.stat(self.filter).st_mtime
        except OSError:
            return []

        if st_mtime > self._last_mtime:
            try:
                with open(self.filter) as fp:
                    self._pids = fp.readlines()
                    self._last_mtime = st_mtime
            except IOError:
                return []

        return self._pids


class EXEFilter(Filter):
    @staticmethod
    def is_compatible(filter_string):
        return isinstance(filter_string, basestring)

    def _filter(self, on):
        try:
            return fnmatch(os.path.realpath(os.path.join(on, 'exe')), self.filter)
        except OSError:
            return False


class CMDLineFilter(Filter):
    def __init__(self, filter):
        super(CMDLineFilter, self).__init__(filter)

        self.filter_re = re.compile(self.filter)

    @staticmethod
    def is_compatible(filter_string):
        try:
            re.compile(filter_string)
        except re.error:
            return False
        else:
            return True

    def _filter(self, on):
        with open(os.path.join(on, 'cmdline')) as fp:
            cmdline = fp.read().strip()

        cmdline = ' '.join(cmdline.split('\x00'))
        return self.filter_re.search(cmdline) is not None


FILTERS = {
    'pidfile': PIDFileFilter,
    'exe': EXEFilter,
    'cmdline': CMDLineFilter,
}

_CLOCK_RATE = os.sysconf(os.sysconf_names['SC_CLK_TCK'])
_NUM_CPUS = os.sysconf('SC_NPROCESSORS_ONLN')


def get_proc_jiffies(pid):
    with open('/proc/%s/stat' % pid) as proc_stat:
        stat = proc_stat.read().strip()

    stat = stat[stat.find(')') + 2:]
    vals = stat.split(' ')

    ujiffies = float(vals[11]) / _CLOCK_RATE
    sjiffies = float(vals[12]) / _CLOCK_RATE

    return ujiffies + sjiffies


def get_system_jiffies():
    with open('/proc/stat') as proc_stat:
        stat = proc_stat.read().split()

    stat = stat[1:8]
    return sum([float(s) / _CLOCK_RATE for s in stat])


class CPUByProcessPlugin(PorkchopPlugin):
    __cache = defaultdict(dict)

    def get_data(self):
        filters = {}
        for process, mask in self.config.get('processes', {}).iteritems():
            if ':' not in mask:
                continue

            filter_type, filter_string = mask.split(':', 1)

            if filter_type not in FILTERS:
                continue

            if FILTERS[filter_type].is_compatible(filter_string):
                filters[process] = FILTERS[filter_type](filter_string)

        if not filters:
            return {}

        data = defaultdict(float)

        for proc in os.listdir('/proc'):
            proc_path = os.path.join('/proc', proc)
            if not os.path.isdir(proc_path) or not proc.isdigit():
                continue

            for name, proc_filter in filters.iteritems():
                if proc_filter.match(proc_path):
                    if proc not in self.__cache:
                        self.__cache[proc]['proc'] = get_proc_jiffies(proc)
                        self.__cache[proc]['sys'] = get_system_jiffies()
                        sleep(0.1)

                    proc_jiffies = get_proc_jiffies(proc)
                    sys_jiffies = get_system_jiffies()

                    delta_proc = proc_jiffies - self.__cache[proc]['proc']
                    delta_sys = sys_jiffies - self.__cache[proc]['sys']

                    if delta_proc < 0.0:
                        sleep(0.1)
                        delta_proc = get_proc_jiffies(proc) - proc_jiffies
                        delta_sys = get_system_jiffies() - sys_jiffies

                    try:
                        data[name] += (delta_proc / delta_sys) * 100.0 * _NUM_CPUS
                    except ZeroDivisionError:
                        data[name] += 0.0

        return data
