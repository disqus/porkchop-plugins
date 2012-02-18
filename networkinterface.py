import os.path

from porkchop.plugin import PorkchopPlugin


class NetworkinterfacePlugin(PorkchopPlugin):
    def format_data(self, data):
        result = self.gendict()
        prev = self.prev_data

        for iface, iface_data in data.iteritems():
            for typ, typ_data in iface_data.iteritems():
                for stat, value in typ_data.iteritems():
                    label = '%s_per_second' % stat
                    result[iface][typ][label] = self.rateof(prev[iface][typ][stat],
                                                    value)

        return result

    def get_data(self):
        script = '/proc/net/dev'

        if not os.path.exists(script):
            return {}

        data = self.gendict()

        with open(script, 'r') as f:
            output = f.readlines()

            output.pop(0)

            keys = output[0].replace('|', ' ').split()[1:]
            recv_keys = tuple(keys[0:8])
            xmit_keys = tuple(keys[8:])

            for line in output[1:]:
                (iface, fields) = line.strip().split(':')
                fields = fields.split()
                recv_tup = tuple(fields[0:8])
                xmit_tup = tuple(fields[8:])
                data[iface]['recv'] = dict(zip(recv_keys, recv_tup))
                data[iface]['xmit'] = dict(zip(xmit_keys, xmit_tup))

        return data
