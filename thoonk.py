import redis
from porkchop.plugin import PorkchopPlugin


class ThoonkPlugin(PorkchopPlugin):

    def get_data(self):

        self.client = redis.StrictRedis(
            self.config['host'],
            self.config['port'],
            self.config.get('db', 0)
        )

        feeds = self.client.smembers('feeds')
        if not len(feeds):
            raise Exception("Thoonk doesn't appear to be running.")

        data = {}
        for feed in feeds:
            data[feed] = self._feed_data(feed)

        return data

    def _feed_data(self, feed):
        cancelled = self.client.hvals('feed.cancelled:' + feed)
        claimed = self.client.zrange('feed.claimed:' + feed, 0, -1)
        stalled = self.client.smembers('feed.stalled:' + feed)
        return {
            'backlog': self.client.llen("feed.ids:test") or 0,
            'publishes': self.client.get('feed.publishes:' + feed) or 0,
            'finishes': self.client.get('feed.finishes:' + feed) or 0,
            'claimed': len(claimed or []),
            'stalled': len(stalled or []),
            'cancelled_jobs': len(cancelled),
            'cancelled_count': sum(map(int,cancelled))
        }
