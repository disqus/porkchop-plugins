import json
import urllib2
from porkchop.plugin import PorkchopPlugin

class RiakPlugin(PorkchopPlugin):
  def get_data(self):
    stats_url = self.config.get('riak', {}).get('stats_url',
      'http://localhost:8098/stats')

    stats = json.loads(urllib2.urlopen(stats_url).read())

    for key in stats.keys():
      if type(stats[key]) == list:
        stats[key] = ', '.join(stats[key])

    return stats
