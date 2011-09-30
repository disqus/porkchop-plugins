import re
from subprocess import Popen, PIPE

from porkchop.plugin import PorkchopPlugin

def df(cmd):
  data = {}
  r1 = re.compile('^/(dev/|)')

  output = Popen([cmd], stdout=PIPE, shell=True).communicate()[0].splitlines()

  output.pop(0)
  for line in output:
    fields = line.split()
    key = r1.sub('', fields[0]).replace('/', '_')
    data[key] = {
      'total': fields[1],
      'used': fields[2],
      'available': fields[3],
      'percent_used': fields[4].replace('-', '0').replace('%', ''),
      'mountpoint': fields[5]
    }

  return data

class DfPlugin(PorkchopPlugin):
  def get_data(self):
    data = {}
    cmd = 'df -l'
    excludefs = [
      'debugfs',
      'devtmpfs',
      'ecryptfs',
      'iso9660',
      'none',
      'ramfs',
      'romfs',
      'squashfs',
      'simfs'
      'udf',
      'unknown',
      'tmpfs'
    ]

    blocks_cmd = '%s -x %s' % (cmd, ' -x '.join(excludefs))
    inodes_cmd = '%s -i -x %s' % (cmd, ' -x '.join(excludefs))

    blocks = df(blocks_cmd)
    for key in blocks:
      data.setdefault(key, {})
      data[key]['mountpoint'] = blocks[key]['mountpoint']
      del blocks[key]['mountpoint']
      data[key]['blocks'] = blocks[key]

    inodes = df(inodes_cmd)
    for key in inodes:
      data.setdefault(key, {})
      del inodes[key]['mountpoint']
      data[key]['inodes'] = inodes[key]

    return data
