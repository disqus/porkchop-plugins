import socket

from porkchop.plugin import PorkchopPlugin

class MemcachedPlugin(PorkchopPlugin):
  def _connect(self, host, port):
    try:
      sock = socket.socket()
      sock.connect((host, port))
    except:
      raise

    return sock

  def get_data(self):
    data = {}
    resp_data = ''

    try:
      instance_config = self.config['memcached']['instances']
    except:
      instance_config = 'localhost:11211'

    instances = [s.strip().split(':') for s in instance_config.split(',')]

    for host, port in instances:
      try:
        sock = self._connect(host, int(port))

        sock.send('stats\r\nquit\r\n')

        while not resp_data.endswith('END\r\n'):
          resp_data += sock.recv(1024)

        sock.close()
      except socket.error:
        continue

      for line in resp_data.splitlines():
        if not line.startswith('STAT'): continue
        trash, k, v = line.split()
        data[k] = v

    return data
