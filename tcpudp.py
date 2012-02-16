from subprocess import Popen, PIPE

from porkchop.plugin import PorkchopPlugin


class TcpudpPlugin(PorkchopPlugin):
    def get_data(self):
        command = 'ss -tuna'
        data = self.gendict()

        proc = Popen([command], stdout=PIPE, stderr=PIPE, shell=True)
        output = proc.communicate()[0].splitlines()
        if proc.returncode != 0:
            return {}

        output.pop(0)

        for line in output:
            fields = line.split()
            proto = fields[0]

            if proto == 'tcp':
                state = fields[1].lower()
                data[proto][state].setdefault('value', 0)
                data[proto][state]['value'] += 1
            else:
                data[proto].setdefault('value', 0)
                data[proto]['value'] += 1

        return dict(data)
