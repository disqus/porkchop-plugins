import os.path

from porkchop.plugin import PorkchopPlugin


class NetprotoPlugin(PorkchopPlugin):
    def get_data(self):
        script = '/proc/net/snmp'

        if not os.path.exists(script):
            return {}

        data = self.gendict()
        with open(script, 'r') as f:
            for line in f:
                fields = line.split()
                proto = fields[0].lower().rstrip(':')

                if not proto in data.keys():
                    keys = [fld.lower() for fld in fields[1:]]
                data[proto] = {}
            else:
                data[proto] = dict(zip(keys, tuple(fields[1:])))

        return data

    def format_data(self, data):
        result = {}
        prev = self.prev_data

        for proto in data.iterkeys():
            result.setdefault(proto, {})
            for stat in data[proto].iterkeys():
                result[proto][stat] = self.rateof(prev[proto][stat],
                                                  data[proto][stat])

        return result
