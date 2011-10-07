import glob
import time

from porkchop.plugin import PorkchopPlugin

def sub(a, b, inter):
  return (b - a) / inter if (b - a) > 0 else 0

def read_info():
  count = None

  f = open('/proc/stat', 'r')

  for line in f:
    if line.startswith('processes'):
      count = line.split()[1]

  f.close()
  return int(count)

class ProcessesPlugin(PorkchopPlugin):
  def get_data(self):
    data = {}

    data['count'] = len(glob.glob('/proc/[1-9]*'))

    import pdb
    pdb.set_trace()
    if not self.__class__._cache:
      prev = read_info()
      delta = 1
      time.sleep(delta)
    else:
      prev = self.__class__._cache
      delta = int(time.time() - self.__class__._lastrefresh)

    self.__class__._cache = cur = read_info()

    data['forkrate'] = sub(prev, cur, delta)

    return data
