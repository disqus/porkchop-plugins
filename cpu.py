import os
import time

from porkchop.plugin import PorkchopPlugin

def jiffyize(val1, val2):
  jiffy = os.sysconf(os.sysconf_names['SC_CLK_TCK'])

  return (float(val2) - float(val1)) * 100 / jiffy

def read_info():
  data = {}

  f = open('/proc/stat', 'r')

  for line in f:
    if line.startswith('cpu'):
      fields = line.split()
      data[fields[0]] = fields[1:]
    else:
      break

  f.close()
  return data

class CpuPlugin(PorkchopPlugin):
  def get_data(self):
    data = {}

    fields = [
      'user',
      'nice',
      'system',
      'idle',
      'iowait',
      'irq',
      'softirq'
    ]

    hz = os.sysconf(os.sysconf_names['SC_CLK_TCK'])

    cpu_first = read_info()
    time.sleep(1)
    cpu_second = read_info()

    for key in cpu_second.keys():
      data.setdefault(key, {})
      for pos in xrange(len(fields)):
        fname = fields[pos]
        data[key].update({
          fname: jiffyize(cpu_first[key][pos], cpu_second[key][pos])
        })

    return data
