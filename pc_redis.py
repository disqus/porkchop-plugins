import redis

from porkchop.plugin import PorkchopPlugin


class PCRedisPlugin(PorkchopPlugin):

    __metric_name__ = 'redis'

    def _connect(host, port):
        return redis.StrictRedis(host, port, 0)

    def _instances(self):
        instance_config = self.config.get('redis', {}).get('instances',
                                                           'localhost:6379')
        return [s.strip().split(':') for s in instance_config.split(',')]

    def _get_info(self, client):
        return client.info()

    def _get_thoonk(self, client):

        feeds = self.client.smembers('feeds')
        if not len(feeds):
            raise Exception("Thoonk doesn't appear to be running.")

        data = {}
        for feed in feeds:
            data[feed] = self._thoonk_feed_data(feed, client)

        return data

    def _thoonk_feed_data(self, feed, client):
        cancelled = client.hvals('feed.cancelled:' + feed)
        claimed = client.zrange('feed.claimed:' + feed, 0, -1)
        stalled = client.smembers('feed.stalled:' + feed)
        return {
            'backlog': client.llen('feed.ids:' + feed) or 0,
            'publishes': client.get('feed.publishes:' + feed) or 0,
            'finishes': client.get('feed.finishes:' + feed) or 0,
            'claimed': len(claimed or []),
            'stalled': len(stalled or []),
            'cancelled_jobs': len(cancelled),
            'cancelled_count': sum(map(int, cancelled))
        }

    def get_data(self):
        data = {}

        for host, port in self._instances():
            client = self._connect(host, port)
            cdata = {}
            cdata = self._get_info(client)
            cdata['thoonk'] = self._get_thoonk(client)
            data[port] = cdata

        return data
