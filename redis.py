import socket

from porkchop.plugin import PorkchopPlugin

class RedisPlugin(PorkchopPlugin):
  def _connect(self, host, port):
    try:
      sock = socket.socket()
      sock.connect((host, port))
    except:
      raise

    return sock

  def get_data(self):
    data = self.gendict()

    instance_config = self.config.get('redis', {}).get('instances',
      'localhost:6379')

    instances = [s.strip().split(':') for s in instance_config.split(',')]

    for host, port in instances:
      try:
        sock = self._connect(host, int(port))
        sock.send('info\r\n')

        # first line is the response length in bytes
        resp_hdr = ''
        sock.recv(1)
        while not resp_hdr.endswith('\r\n'):
          resp_hdr += sock.recv(1)

        resp_len = int(resp_hdr.strip())

        resp_data = sock.recv(resp_len)
        sock.send('quit\r\n')
        sock.close()
      except (socket.error, ValueError):
        continue

      for line in resp_data.splitlines():
        # apparently some versions of redis have comments and empty lines
        if not line or line.startswith('#'):
          continue

        k, v = line.split(':', 1)

        # some stat values are CSV, k/v delimited with an '='
        # one of them is allocation_stats but its format is
        # all fucked up
        if ',' in v and k != 'allocation_stats':
          for stat in v.split(','):
            k2, v2 = stat.split('=')
            data[port][k][k2] = v2
        else:
          data[port][k] = v

    return data
