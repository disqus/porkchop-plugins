import json
import socket

from collections import Mapping

from porkchop.plugin import PorkchopPlugin


class PostfixStatsPlugin(PorkchopPlugin):
    def get_data(self):
        instance_config = self.config.get('postfix-stats', {}).get('instance',
            'localhost:7777')
        client_min_conns = self.config.get('postfix-stats', {}).get('client-min-conns',
            100)
        host, port = instance_config.split(':')

        s = socket.socket()

        json_data = ''
        try:
            s.connect((host, int(port)))
            s.sendall('stats\n')

            while 1:
                raw_data = s.recv(1024)
                if not raw_data:
                    break
                json_data += raw_data
        except socket.error:
            pass
        finally:
            s.close()

        data = json.loads(json_data)

        # Filter clients with less than X connections
        data['clients'] = dict((k, v) for k, v in data['clients'].iteritems() if v > client_min_conns)

        return data

    def format_data(self, data):
        results = self._calc_rateof(data, self.prev_data)

        # Convert dots to underscores for graphite compatibility
        dots_to_unders = {ord(u'.'): u'_'}
        data['clients'] = dict((k.translate(dots_to_unders), v) for k, v in data['clients'].iteritems())

        # Remove . from resp_codes
        dots_to_none = {ord(u'.'): None}
        for sect in (u'in', u'recv', u'send'):
            resp_codes = results[sect]['resp_codes']
            for k in resp_codes.keys():
                resp_codes[k.translate(dots_to_none)] = resp_codes.pop(k)

        return results

    def _calc_rateof(self, data, p_data, path=None):
        if path is None:
            path = []

        res = {}

        for k, v in data.iteritems():
            path.append(k)

            if isinstance(v, Mapping):
                rate = self._calc_rateof(v, p_data, path)
            else:
                p_val = p_data
                try:
                    for p in path:
                        p_val = p_val[p]
                except KeyError:
                    p_val = 0

                rate = self.rateof(p_val, v)

            res[path.pop()] = rate

        return res
