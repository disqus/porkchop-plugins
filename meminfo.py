from porkchop.plugin import PorkchopPlugin

class MeminfoPlugin(PorkchopPlugin):
  def get_data(self):
    data = {}
    f = open('/proc/meminfo', 'r')

    for line in f:
      lhs, rhs = line.split(':')
      lhs = lhs.replace('(', '_').replace(')', '').lower()
      data[lhs] = rhs.strip().split()[0]

    return data
