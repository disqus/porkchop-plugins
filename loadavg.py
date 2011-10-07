from porkchop.plugin import PorkchopPlugin

class LoadavgPlugin(PorkchopPlugin):
  def get_data(self):
    with open('/proc/loadavg', 'r') as f:
      fields = f.read().strip().split()
      procs = fields[3].split('/')

    return {
      'shortterm': fields[0],
      'midterm': fields[1],
      'longterm': fields[2],
      'processes': {
        'scheduled': procs[0],
        'total': procs[1]
      }
    }
