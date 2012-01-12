import re
import socket

from porkchop.plugin import PorkchopPlugin

HAPROXY_SOCKET = '/var/run/haproxy.socket'

class HAProxy(object):
  @classmethod
  def col2stat(self, idx):
    try:
      ret = {
        0: 'vip_name', 1: 'backend_name', 2: 'queue_cur',
        3: 'queue_max', 4: 'sessions_cur', 5: 'sessions_max',
        6: 'sessions_limit', 7: 'sessions_total', 8: 'bytes_in',
        9: 'bytes_out', 10: 'denied_req', 11: 'denied_resp',
        12: 'errors_req', 13: 'errors_conn', 14: 'errors_resp',
        15: 'warnings_retr', 16: 'warnings_redis', #17: 'server_status',
        18: 'server_weight', 19: 'server_active', 20: 'server_backup',
        21: 'server_check', 22: 'server_down', 23: 'server_lastchange',
        24: 'server_downtime', 25: 'queue_limit', 29: 'server_throttle',
        30: 'sessions_lbtotal', 32: 'session_type', 33: 'session_rate_cur',
        34: 'session_rate_limit', 35: 'session_rate_max'
      }[idx]
    except KeyError:
      ret = None

    return ret

  @classmethod
  def stats(self, sock_path):
    try:
      sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
      sock.settimeout(3)
      sock.connect(sock_path)
      sock_data = []
      data = ''

      sock.send('show stat\n')

      while True:
        data = sock.recv(1024)
        if not data: break
        sock_data.append(data)

      sock.close()
    except socket.error:
      return []

    return ''.join(sock_data).strip('\n').splitlines()

class HaproxyPlugin(PorkchopPlugin):
  def get_data(self):
    all_stats = []
    d1 = self.gendict()
    r1 = re.compile('^(#|$)')

    for line in HAProxy.stats(HAPROXY_SOCKET):
      if r1.match(line): continue

      lary = line.split(',')
      stat = {}

      for i in xrange(0,len(lary)-1):
        if not lary[i]: lary[i] = None
        stat.update({HAProxy.col2stat(i): lary[i]})

      try:
        del stat[None]
      except:
        pass

      all_stats.append(stat)

    for x in all_stats:
      for key, val in x.iteritems():
        r2 = re.compile('_name')
        d1[x['vip_name']][x['backend_name']][key] = val

    return d1
