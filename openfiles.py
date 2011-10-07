from porkchop.plugin import PorkchopPlugin

class OpenfilesPlugin(PorkchopPlugin):
  def get_data(self):
    with open('/proc/sys/fs/file-nr', 'r') as f:
      fields = f.read().split()

    data = {
      'count': int(fields[0]) - int(fields[1]),
      'max': fields[2]
    }

    return data
