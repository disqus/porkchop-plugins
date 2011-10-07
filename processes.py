import glob
import time

from porkchop.plugin import PorkchopPlugin

def sub(a, b, inter):
  return (b - a) / inter if (b - a) > 0 else 0

def processes_count():
  count = 0

  f = open('/proc/stat', 'r')

  for line in f:
    if line.startswith('processes'):
      count = int(line.split()[1])

  f.close()
  return count

def thread_count(f):
  threads = 0

  try:
    f = open(f, 'r')
  except IOError:
    pass

  for line in f:
    if line.startswith('Threads:'):
      count = int(line.split()[1])

  f.close()
  return count

class ProcessesPlugin(PorkchopPlugin):
  def get_data(self):
    data = {}

    data['count'] = data['threads'] = 0
    for piddir in glob.glob('/proc/[1-9]*'):
      data['count'] += 1
      data['threads'] += thread_count('%s/status' % piddir)

    if not self.__class__._cache:
      prev = processes_count()
      delta = 1
      time.sleep(delta)
    else:
      prev = self.__class__._cache
      delta = int(time.time() - self.__class__._lastrefresh)

    self.__class__._cache = cur = processes_count()

    data['forkrate'] = sub(prev, cur, delta)

    return data
