import requests

from porkchop.plugin import PorkchopPlugin

class ApachePlugin(PorkchopPlugin):
  def parse_scoreboard(self, scoreboard):
    sb = {}
    scoreboard_keys = {
      '_': 'waiting',
      'S': 'starting',
      'R': 'reading',
      'W': 'sending',
      'K': 'keepalive',
      'D': 'dnslookup',
      'C': 'closing',
      'L': 'logging',
      'G': 'finishing',
      'I': 'idle_cleanup',
      '.': 'open'
    }

    for chr in list(scoreboard):
      sb.setdefault(scoreboard_keys[chr], 0)
      sb[scoreboard_keys[chr]] += 1

    return sb

  def get_data(self):
    data = {}

    r = requests.get('http://localhost/server-status?auto')
    for line in r.content.strip('\n').splitlines():
      (key, val) = line.split(':', 1)

      if key == 'Scoreboard':
        data['scoreboard'] = self.parse_scoreboard(val.strip())
      else:
        data[key.replace(' ', '_').lower()] = val.strip()

    return data
