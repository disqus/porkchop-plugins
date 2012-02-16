import copy
import glob
import os.path

from porkchop.plugin import PorkchopPlugin


class ProcessesPlugin(PorkchopPlugin):
    def get_thread_count(self, f):
        count = 0

        try:
            with open(f, 'r') as f:
                for line in f:
                    if line.startswith('Threads:'):
                        count = int(line.split()[1])
        except IOError:
            pass

        return count

    def get_processes_count(self):
        count = 0

        script = '/proc/stat'
        if not os.path.exists(script):
            return None

        with open(script, 'r') as f:
            for line in f:
                if line.startswith('processes'):
                    count = int(line.split()[1])

        return count

    def get_data(self):
        data = {}

        data['count'] = data['threads'] = 0
        for piddir in glob.glob('/proc/[1-9]*'):
            data['count'] += 1
            data['threads'] += self.get_thread_count('%s/status' % piddir)

        data['processes'] = self.get_processes_count()

        return data

    def format_data(self, data):
        result = copy.deepcopy(data.copy)
        prev = self.prev_data

        if data['processes']:
            result['forkrate'] = self.rateof(prev['processes'], data['processes'])

        return result
