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
  recv_stat_fields = [
    'bytes',
    'packets',
    'errs',
    'drop',
    'fifo',
    'frame',
    'compressed',
    'multicast'
  ]
  xmit_stat_fields = [
    'bytes',
    'packets',
    'errs',
    'drop',
    'fifo',
    'colls',
    'carrier',
    'compressed'
  ]

  f = open('/proc/net/dev', 'r')
  output = f.readlines()
  output.pop(0); output.pop(0)

  for line in output:
    fields = line.split()
    interface = fields.pop(0).strip()
    interface = interface[0:len(interface)-1]

    for pos in xrange(len(recv_stat_fields)):
      stat = recv_stat_fields[pos]
      data[interface]['recv'][stat] = fields[pos]

    for pos in xrange(len(xmit_stat_fields)):
      stat = xmit_stat_fields[pos]
      data[interface]['xmit'][stat] = fields[pos+len(recv_stat_fields)]

  return data

class NetworkinterfacePlugin(PorkchopPlugin):
  def __init__(self):
    self.refresh = 1

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
          data[iface][typ]['%s_per_second' % stat] = sub(prev[iface][typ][stat],
                                                         cur[iface][typ][stat],
                                                         delta)

    return data
