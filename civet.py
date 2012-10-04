import json
import socket

from porkchop.plugin import PorkchopPlugin


class CivetPlugin(PorkchopPlugin):
    def get_data(self):
        instance_config = self.config.get('civet', {}).get('instance', 'localhost:7201')
        host, port = instance_config.split(':')

        json_data = ''
        s = socket.create_connection((host, int(port)), timeout=1)

        try:
            s.sendall('sample\n')

            while 1:
                raw_data = s.recv(1024)
                if not raw_data:
                    break
                json_data += raw_data
        except socket.error:
            pass
        finally:
            s.close()

        raw_data = json.loads(json_data)

        data = self.gendict('dot')
        for k, v in raw_data.iteritems():
            data[k] = v

        return data
