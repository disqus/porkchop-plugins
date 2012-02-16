import os.path

from porkchop.plugin import PorkchopPlugin


class MeminfoPlugin(PorkchopPlugin):
    def get_data(self):
        script = '/proc/meminfo'

        if not os.path.exists(script):
            return {}

        data = {}
        with open(script, 'r') as f:
            for line in f:
                lhs, rhs = line.split(':')
                lhs = lhs.replace('(', '_').replace(')', '').lower()
                data[lhs] = rhs.strip().split()[0]

        data['memused'] = int(data['memtotal']) - \
                     (int(data['memfree']) + \
                      int(data['buffers']) + \
                      int(data['cached']))
        data['swapused'] = int(data['swaptotal']) - int(data['swapfree'])

        return data
