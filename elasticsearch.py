import json
import requests
from porkchop.plugin import PorkchopPlugin

class ElasticsearchPlugin(PorkchopPlugin):
  def get_data(self):
    stats_url = self.config.get('elasticsearch', {}).get('stats_url',
      'http://localhost:9200/_cluster/nodes/_local/stats')

    raw_stats = json.loads(requests.get(stats_url).content)

    # raw_stats['nodes'][<HASH>]
    # The <HASH> is generated at server start and since it is the only key
    #   just list keys and grab the first one
    return { raw_stats['cluster_name']: raw_stats['nodes'][raw_stats['nodes'].keys()[0]] }
