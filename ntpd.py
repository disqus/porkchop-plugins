from subprocess import Popen, PIPE

from porkchop.plugin import PorkchopPlugin


class NtpdPlugin(PorkchopPlugin):
    @staticmethod
    def ntpq_data():
        data = {}

        cmd = ['/usr/bin/ntpq', '-np']
        output = Popen(cmd, stdout=PIPE).communicate()[0].splitlines()

        for line in output:
            # Only care about system peer
            if not line.startswith('*'):
                continue

            parts = line[1:].split()

            data['stratum'] = parts[2]
            data['when'] = parts[4]
            data['poll'] = parts[5]
            data['reach'] = parts[6]
            data['delay'] = parts[7]
            data['offset'] = parts[8]
            data['jitter'] = parts[9]

        return data

    @staticmethod
    def ntpdc_data():
        data = {}

        cmd = ['/usr/bin/ntpdc', '-c', 'kerninfo']
        output = Popen(cmd, stdout=PIPE).communicate()[0].splitlines()

        for line in output:
            key, val = line.split(':')
            val = float(val.split()[0])

            if key == 'pll offset':
                data['offset'] = val
            elif key == 'pll frequency':
                data['frequency'] = val
            elif key == 'maximum error':
                data['max_error'] = val
            elif key == 'estimated error':
                data['est_error'] = val

        return data

    def get_data(self):
        data = {}
        data.update(self.ntpq_data())
        data.update(self.ntpdc_data())

        return data
