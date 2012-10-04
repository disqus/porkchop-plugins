import json
import urllib2

from porkchop.plugin import PorkchopPlugin


class NginxHttpPushStreamPlugin(PorkchopPlugin):
    METRIC_KEYS = frozenset(['channels', 'broadcast_channels', 'published_messages', 'subscribers', 'uptime'])

    def get_data(self):
        f = urllib2.urlopen('http://127.0.0.1/status', timeout=1)

        try:
            raw_data = json.load(f)
        except ValueError:
            return {}

        data = dict((k, v) for k, v in raw_data.iteritems() if k in self.METRIC_KEYS)

        return data
