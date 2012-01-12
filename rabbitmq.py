from porkchop.plugin import PorkchopPlugin
import json
import requests
from subprocess import Popen, PIPE


class RabbitmqPlugin(PorkchopPlugin):
    """Try to use web plugin, otherwise fall back to the cli"""

    def use_api(self):
        api = RabbitmqWeb(self.host, self.port, self.user, self.passwd)
        return api.get_data()

    def use_cli(self):
        cli = RabbitmqCli()
        return cli.get_data()

    def get_data(self):
        config = self.config.get('rabbitmq', {})
        self.user = config.get('user', 'guest')
        self.passwd = config.get('passwd', 'guest')
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 5672)

        try:
            return self.use_api()
        except:
            return self.use_cli()


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


class RabbitmqWeb(object):
    """RabbitMQ status using the management API.
    requires http://www.rabbitmq.com/management.html
    """

    def __init__(self, host, port, user, passwd):
        self.user = user
        self.passwd = passwd
        self.host = host
        self.port = port
        self.url = self.construct_url()
        self.try_api()

    def try_api(self):
        test_url = "%s/aliveness-test/%%2F" % self.url
        r = requests.get(test_url, auth=(self.user, self.passwd))

        r.raise_for_status()

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
