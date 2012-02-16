import os

from porkchop.plugin import PorkchopPlugin


class CpuPlugin(PorkchopPlugin):
    def get_data(self):
        script = '/proc/stat'

        if not os.path.exists(script):
            return {}

        data = {}

        with open(script, 'r') as f:
            for line in f:
                if line.startswith('cpu'):
                    fields = line.split()
                    data[fields[0]] = fields[1:]
                else:
                    break

        return data

    def format_data(self, data):
        result = {}
        prev = self.prev_data

        fields = [
          'user',
          'nice',
          'system',
          'idle',
          'iowait',
          'irq',
          'softirq'
        ]

        # hz = os.sysconf(os.sysconf_names['SC_CLK_TCK'])

        for key in data.iterkeys():
            result.setdefault(key, {})
            for pos in xrange(len(fields)):
                fname = fields[pos]
                result[key].update({
                    fname: self.rateof(prev[key][pos], data[key][pos])
                })

        return result

    def rateof(self, a, b):
        jiffy = os.sysconf(os.sysconf_names['SC_CLK_TCK'])

        return (float(b) - float(a)) / self.delta * 100 / jiffy
