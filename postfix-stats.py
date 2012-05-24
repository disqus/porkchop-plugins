import json
import socket

from porkchop.plugin import PorkchopPlugin


class PostfixStatsPlugin(PorkchopPlugin):
    def get_data(self):
        instance_config = self.config.get('postfix-stats', {}).get('instance',
            'localhost:7777')
        client_min_conns = self.config.get('postfix-stats', {}).get('client-min-conns',
            100)
        host, port = instance_config.split(':')

        s = socket.socket()

        try:
            s.connect((host, int(port)))
            s.sendall('stats\n')

            json_data = ''
            while 1:
                raw_data = s.recv(1024)
                if not raw_data: break
                json_data += raw_data
        except socket.error:
            pass
        finally:
            s.close()

        data = json.loads(json_data)

        # Filter clients with less than X connections
        dots_to_unders = {ord(u'.'): u'_'}
        for k, v in data['clients'].items():
            data['clients'].pop(k)

            if v < client_min_conns:
                continue

            data['clients'][k.translate(dots_to_unders)] = v

        # Remove . from resp_codes
        dots_to_none = {ord(u'.'): None}
        for sect in (u'in', u'recv', u'send'):
            resp_codes = data[sect]['resp_codes']
            for k in resp_codes.keys():
                resp_codes[k.translate(dots_to_none)] = resp_codes.pop(k)

        return data
