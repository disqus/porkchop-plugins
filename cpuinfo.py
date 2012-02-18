import os.path
import re

from porkchop.plugin import PorkchopPlugin


class CpuinfoPlugin(PorkchopPlugin):
    def get_data(self):
        script = '/proc/cpuinfo'

        if not os.path.exists(script):
            return {}

        d1 = {}
        r1 = re.compile('(\w+)\s+:\s+(\w+)')

        with open(script, 'r') as f:
            for line in f:
                match = r1.match(line)
                if match:
                    k = match.group(1)
                    v = match.group(2)
                if k == 'processor':
                    proc = v
                    d1['processor%s' % proc] = {}
                else:
                    d1['processor%s' % proc].update({k: v})

        return d1
