import time

from porkchop.plugin import PorkchopPlugin

def sub(a, b, inter):
  return (int(b) - int(a)) / inter if (int(b) - int(a)) > 0 else 0

def read_info():
  data = {}
  f = open('/proc/net/snmp', 'r')

  for line in f:
    fields = line.split()
    proto = fields[0].lower().rstrip(':')

    if not proto in data.keys():
      data.setdefault(proto, {})
      keys = [fld.lower() for fld in fields[1:]]
    else:
      data[proto] = dict(zip(keys, tuple(fields[1:])))

  return data

class NetprotoPlugin(PorkchopPlugin):
  def get_data(self):
    data = {}

    if not self.__class__._cache:
      prev = read_info()
      delta = 1
      time.sleep(delta)
    else:
      prev = self.__class__._cache
      delta = int(time.time() - self.__class__._lastrefresh)

    self.__class__._cache = cur = read_info()

    for proto in cur.keys():
      data.setdefault(proto, {})
      for stat in cur[proto].keys():
        data[proto][stat] = sub(prev[proto][stat],
                                cur[proto][stat],
                                delta)

    return data
