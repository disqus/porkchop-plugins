from collections import defaultdict
import time

from porkchop.plugin import PorkchopPlugin

class NetworkinterfacePlugin(PorkchopPlugin):
  def get_data(self):
    data = self.gendict()

    if not self.__class__._cache:
      prev = self._read_info()
      delta = 1
      time.sleep(delta)
    else:
      prev = self.__class__._cache
      delta = int(time.time() - self.__class__._lastrefresh)

    self.__class__._cache = cur = self._read_info()

    for iface in cur.keys():
      for typ in cur[iface].keys():
        for stat in cur[iface][typ].keys():
          label = '%s_per_second' % stat
          data[iface][typ][label] = self.rateof(prev[iface][typ][stat],
                                                cur[iface][typ][stat],
                                                delta)

    return data

  def _read_info(self):
    data = self.gendict()

    with open('/proc/net/dev', 'r') as f:
      output = f.readlines()

    output.pop(0)

    keys = output[0].replace('|',' ').split()[1:]
    recv_keys = tuple(keys[0:8])
    xmit_keys = tuple(keys[8:])

    for line in output[1:]:
      (iface, fields) = line.strip().split(':')
      fields = fields.split()
      recv_tup = tuple(fields[0:8])
      xmit_tup = tuple(fields[8:])
      data[iface]['recv'] = dict(zip(recv_keys, recv_tup))
      data[iface]['xmit'] = dict(zip(xmit_keys, xmit_tup))

    return data
