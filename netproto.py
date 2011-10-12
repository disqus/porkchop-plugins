import time

from porkchop.plugin import PorkchopPlugin

class NetprotoPlugin(PorkchopPlugin):
  def get_data(self):
    data = {}

    if not self.__class__._cache:
      prev = self._read_info()
      delta = 1
      time.sleep(delta)
    else:
      prev = self.__class__._cache
      delta = int(time.time() - self.__class__._lastrefresh)

    self.__class__._cache = cur = self._read_info()

    for proto in cur.keys():
      data.setdefault(proto, {})
      for stat in cur[proto].keys():
        data[proto][stat] = self.rateof(prev[proto][stat],
                                        cur[proto][stat], delta)

    return data

  def _read_info(self):
    data = self.gendict()
    with open('/proc/net/snmp', 'r') as f:
      for line in f:
        fields = line.split()
        proto = fields[0].lower().rstrip(':')

        if not proto in data.keys():
          keys = [fld.lower() for fld in fields[1:]]
          data[proto] = {}
        else:
          data[proto] = dict(zip(keys, tuple(fields[1:])))

    return data
