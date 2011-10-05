from collections import defaultdict
import os
import time

from porkchop.plugin import PorkchopPlugin

def deepDict():
  return defaultdict(deepDict)

def sub(a, b, inter):
  return (int(b) - int(a)) / inter if (int(b) - int(a)) else 0

def read_info():
  data = deepDict()

  f = open('/proc/net/dev', 'r')
  output = f.readlines()
  output.pop(0)

  keys = output[0].replace('|','').split()[1:]
  recv_keys = tuple(keys[0:8])
  xmit_keys = tuple(keys[8:])

  for line in output[1:]:
    fields = line.split()
    iface = fields.pop(0).strip(':')
    recv_tup = tuple(fields[0:8])
    xmit_tup = tuple(fields[8:])
    data[iface]['recv'] = dict(zip(recv_keys, recv_tup))
    data[iface]['xmit'] = dict(zip(xmit_keys, xmit_tup))

  return data

class NetworkinterfacePlugin(PorkchopPlugin):
  def get_data(self):
    data = deepDict()

    if not self.__class__._cache:
      prev = read_info()
      delta = 1
      time.sleep(delta)
    else:
      prev = self.__class__._cache
      delta = int(time.time() - self.__class__._lastrefresh)

    self.__class__._cache = cur = read_info()

    for iface in cur.keys():
      for typ in cur[iface].keys():
        for stat in cur[iface][typ].keys():
          label = '%s_per_second' % stat
          data[iface][typ][label] = sub(prev[iface][typ][stat],
                                        cur[iface][typ][stat],
                                        delta)

    return data
