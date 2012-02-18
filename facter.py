import re
from subprocess import Popen, PIPE

from porkchop.plugin import PorkchopPlugin


class FacterPlugin(PorkchopPlugin):
    def get_data(self):
        d1 = {}
        r1 = re.compile('(.*?)\s=>\s(.*)')

        proc = Popen(['facter'], stdout=PIPE, stderr=PIPE, shell=True)
        output = proc.communicate()[0]
        if proc.returncode != 0:
            return {}

        for line in output.splitlines():
            match = r1.match(line)
            if match:
                d1[match.group(1)] = match.group(2)

        return d1
