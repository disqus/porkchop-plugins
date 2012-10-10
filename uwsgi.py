import json
import socket

from collections import defaultdict

from porkchop.plugin import PorkchopPlugin


class UwsgiPlugin(PorkchopPlugin):
    """ Configure like
    [uwsgi]
    myinst1=localhost:1717
    otherint=localhost:1718
    """
    def get_data(self):
        data = defaultdict(dict)

        for name, instance in self.config.get('uwsgi', {}).iteritems():
            host, port = instance.split(':')

            json_data = ''
            s = socket.create_connection((host, int(port)), timeout=1)

            try:
                while 1:
                    raw_data = s.recv(1024)
                    if not raw_data:
                        break
                    json_data += raw_data
            except socket.error:
                pass
            finally:
                s.close()

            try:
                raw_data = json.loads(json_data)
            except ValueError:
                continue

            inst_data = data[name]
            inst_data['workers'] = defaultdict(dict)

            inst_data['listen_queue'] = raw_data['listen_queue']
            inst_data['listen_queue_errors'] = raw_data['listen_queue_errors']
            inst_data['load'] = raw_data['load']

            for worker in raw_data['workers']:
                worker_data = inst_data['workers'][worker.pop('id')]

                del worker['pid']
                del worker['status']

                apps = worker.pop('apps', [])

                worker_data.update(worker)

                for app in apps:
                    mountpoint = app.pop('mountpoint', 'root')

                    del app['id']
                    del app['chdir']

                    worker_data['apps'][mountpoint].update(app)

        return data
