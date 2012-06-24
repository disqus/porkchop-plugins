from subprocess import Popen, PIPE

from porkchop.plugin import PorkchopPlugin


class WackamolePlugin(PorkchopPlugin):
    def get_owned(self):
        owned = []
        p1 = Popen(["wackatrl -l"], stdout=PIPE, stderr=PIPE, shell=True)
        o1 = p1.communicate()[0].splitlines()
        if p1.returncode != 0:
            return []

        for line in o1:
            ln = line.strip()
            if ln.startswith('Owner'):
                owner = ln.split()[1]
            else:
                data = ln.split()[1]
                iface = data.split(':')[0]
                ip = data.split(':')[1].split('/')[0]

                p2 = Popen(["facter ipaddress_%s" % iface], stdout=PIPE, stderr=PIPE, shell=True)
                o2 = p2.communicate()[0].strip()
                if p2.returncode != 0:
                    continue

                if owner == o2:
                    owned.append(ip)

        return owned

    def get_data(self):
        return {'owned': ','.join(self.get_owned())}
