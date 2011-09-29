import glob

from porkchop.plugin import PorkchopPlugin

class ProcessesPlugin(PorkchopPlugin):
  def get_data(self):
    return {'total': len(glob.glob('/proc/[1-9]*'))}
