from porkchop.plugin import PorkchopPlugin
from porkchop.commandline import get_logger
import json
import requests
from subprocess import Popen, PIPE


class RabbitmqPlugin(PorkchopPlugin):
    """Try to use web plugin, otherwise fall back to the cli"""

    def get_data(self):
        api = RabbitmqWeb()
        log = get_logger('porkchop-collector')
        if api.try_api():
            log.info("rabbitmq - Using web api")
            return api.get_data()

        cli = RabbitmqCli()
        log.info("rabbitmq - Using cli")
        return cli.get_data()


class RabbitmqCli(object):
    """Parse rabbitmqctl for output"""

    def get_vhosts(self):
        return Popen(
          "/usr/sbin/rabbitmqctl list_vhosts",
          stdout=PIPE,
          shell=True
        ).communicate()[0]\
         .strip()\
         .split('\n')[1:-1]

    def get_queues(self, vhost):
        raw_queues = Popen(
          "/usr/sbin/rabbitmqctl list_queues -p %s" % vhost,
          stdout=PIPE,
          shell=True
        ).communicate()[0]\
         .strip()\
         .split('\n')[1:-1]

        queues = {}
        for line in raw_queues:
            try:
                queue, size = line.rsplit('\t', 1)
            except:
                pass
            else:
              queues[queue] = int(size)

        return queues

    def get_data(self):
        output = {}

        for vhost in self.get_vhosts():
            queues = self.get_queues(vhost)
            if vhost == '/':
                vhost = 'default'
            if queues:
                output[vhost] = queues

        return output


class RabbitmqWeb(PorkchopPlugin):
    """RabbitMQ status using the management API.
    requires http://www.rabbitmq.com/management.html

    This can (and should) be subclassed to use your own authentication.

    Something like:

    # myrabbitmqplugin.py
    class MyRabbitmqPlugin(RabbitmqWeb):

        def __init__(self):
            RabbitmqWeb.__init__(self, 'localhost', 55672, 'user', 'passwd')
    """

    def __init__(self, host=None, port=None, user=None, passwd=None):
        self.user = user or 'guest'
        self.passwd = passwd or 'guest'
        self.host = host or 'localhost'
        self.port = port or 55672
        self.url = self.construct_url()
        PorkchopPlugin.__init__(self)

    def try_api(self):
        test_url = "%s/aliveness-test/%%2F" % self.url
        r = requests.get(test_url, auth=(self.user, self.passwd))

        if isinstance(r.error, requests.Timeout) or r.status_code == 401:
            return False
        return True

    def construct_url(self):
        return "http://%s:%s/api" %(self.host, self.port)

    def get_vhosts(self):
        vhosts_url = "%s/vhosts/" % self.url
        response = requests.get(vhosts_url, auth=(self.user, self.passwd))
        vhosts = json.loads(response.content)
        results = [vhost for item in vhosts for name, vhost in item.iteritems()]
        return results

    def get_queues(self, vhost):
        queue_url = "%s/queues/%s" %(self.url, vhost)
        response = requests.get(queue_url, auth=(self.user, self.passwd))
        queues = json.loads(response.content)
        results = dict([(item['name'], item['messages']) for item in queues])
        return results

    def get_data(self):
        output = {}

        for vhost in self.get_vhosts():
            queues = self.get_queues(vhost)
            if vhost == '/':
                vhost = 'default'
            if queues:
                output[vhost] = queues

        return output
