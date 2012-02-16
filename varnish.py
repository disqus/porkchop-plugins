from subprocess import Popen, PIPE

from porkchop.plugin import PorkchopPlugin


class VarnishPlugin(PorkchopPlugin):
    def get_data(self):
        data = {}
        cmd = 'varnishstat -1'
        proc = Popen([cmd], stdout=PIPE, stderr=PIPE, shell=True)
        output = proc.communicate()[0].splitlines()
        if proc.returncode != 0:
            return {}

        for line in output:
            fields = line.split()
            metric = fields[0]
            longterm_rate = fields[2] if fields[2] != '.' else 0
            data[metric] = {
                'counter': fields[1],
                'longterm_per_second': longterm_rate
            }

        return data

    def format_data(self, data):
        result = data.copy()
        prev = self.prev_data

        for metric in data.iterkeys():
            if data[metric]['longterm_per_second'] > 0:
                result[metric]['shortterm_per_second'] = \
                    self.rateof(prev[metric]['counter'],
                                data[metric]['counter'])

        return result
