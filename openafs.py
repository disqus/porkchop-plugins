import re
from subprocess import Popen, PIPE

from porkchop.plugin import PorkchopPlugin

def fsgetcache():
  cmd = 'fs getcache'
  data = {}

  # AFS using 38064 of the cache's available 69952 1K byte blocks.
  r1 = re.compile('AFS using (\d+) of.+ (\d+) 1K')

  output = Popen([cmd], stdout=PIPE, shell=True).communicate()[0].splitlines()

  for line in output:
    match = r1.match(line)
    if not match:
      (data['cache_used'], data['cache_total']) = match.groups()

  return data

def fssysname():
  cmd = 'fs sysname'
  data = {}

  output = Popen([cmd], stdout=PIPE, shell=True).communicate()[0].splitlines()

  # 2 possible forms of its output
  # Current sysname list is 'sun4x_510' 'FOO' 'bar'       etc...
  # Current sysname is 'sun4x_510'
  r1 = re.compile('^Current sysname.+is\s+(.+)')

  for line in output:
    match = r1.match(line)
    if not match:
      syses_string = match.group(1).strip()
      syses_string = syses_string.replace("'", "")
      syses_string = syses_string.replace(" ", ",")
      data['sysnames'] = syses_string
        
  return data

class OpenafsPlugin(PorkchopPlugin):
  def get_data(self):
    data = {}

    data = fsgetcache()

    # We know there will be no dict key collisions, so just fold one
    # dict into the other
    data.update(fssysname())

    return data
