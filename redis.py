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
    data = {}

    try:
      instances = self.config['redis']['instances'].split(',').strip()
    except:
      instances = ['localhost:6379']

    for inst in instances:
      try:
        host, port = inst.split(':')
        sock = self._connect(host, int(port))

        sock.send('info\r\n')

        # first line is the response length in bytes
        resp_hdr = ''
        sock.recv(1)
        while True:
          resp_hdr += sock.recv(1)
          if '\r\n' in resp_hdr: break

        resp_len = int(resp_hdr.strip())

        resp_data = sock.recv(resp_len)
        sock.send('quit\r\n')
        sock.close()
      except socket.error:
        continue

      for line in resp_data.splitlines():
        k, v = line.split(':', 1)

        # some stat values are CSV, k/v delimited with an '='
        # one of them is allocation_stats but its format is
        # all fucked up
        if ',' in v and k != 'allocation_stats':
          data[k] = {}
          for stat in v.split(','):
            k2, v2 = stat.split('=')
            data[k][k2] = v2
        else:
          data[k] = v

    return data
