from subprocess import Popen, PIPE
import time

from porkchop.plugin import PorkchopPlugin

def varnish_stats():
  data = {}
  cmd = 'varnishstat -1'
  output = Popen([cmd], stdout=PIPE, shell=True).\
                 communicate()[0].splitlines()

  for line in output:
    fields = line.split()
    metric = fields[0]
    longterm_rate = fields[2] if fields[2] != '.' else 0
    data[metric] = {
      'counter': fields[1],
      'longterm_per_second': longterm_rate
    }

  return data

class VarnishPlugin(PorkchopPlugin):
  def get_data(self):
    if not self.__class__._cache:
      prev = varnish_stats()
      ival = 1
      time.sleep(ival)
    else:
      prev = self.__class__._cache
      ival = int(time.time() - self.__class__._lastrefresh)

    data = self.__class__._cache = cur = varnish_stats()

    for metric in data.keys():
      if data[metric]['longterm_per_second'] > 0:
        data[metric]['shortterm_per_second'] =\
          self.rateof(prev[metric]['counter'],
                      cur[metric]['counter'], ival)

    return data
