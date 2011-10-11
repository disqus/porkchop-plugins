import glob
import time

from porkchop.plugin import PorkchopPlugin

def processes_count():
  count = 0

  with open('/proc/stat', 'r') as f:
    for line in f:
      if line.startswith('processes'):
        count = int(line.split()[1])

  return count

def thread_count(f):
  threads = 0

  try:
    with open(f, 'r') as f:
      for line in f:
        if line.startswith('Threads:'):
          count = int(line.split()[1])
  except IOError:
    pass

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

    data['forkrate'] = self.rateof(prev, cur, delta)

    return data
