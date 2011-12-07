import time
from subprocess import Popen, PIPE
from string import strip

from porkchop.plugin import PorkchopPlugin

def flatten(d, s=",="):
    if not isinstance(d, dict):
        return str(d)

    if len(s) < 2:
        raise Exception("Requires more separators")

    return s[0].join([s[1].join([k, flatten(v,s[2:])]) for k, v in d.iteritems()])

class PostfixPlugin(PorkchopPlugin):
    @staticmethod
    def get_queue_stats(queue):
        data = {}
        cmd = ' '.join(['qshape', queue])

        output = Popen([cmd], stdout=PIPE, shell=True).communicate()[0].splitlines()

        # Use headers as keys just in case change to linear output
        intervals = [''.join([intv, 'm']) for intv in output[0].split()]
        # "total" makes more sense than "Tm"
        intervals[0] = "total"

        for line in output[1:]:
            fields = line.split()

            domain_metrics = {}
            for i, metric in enumerate(fields[1:]):
                domain_metrics[intervals[i]] = metric

            # fields[0] == domain
            data.update({fields[0]: domain_metrics})

        return data

    def get_data(self):
        queues = frozenset(map(strip, self.config.get('postfix', {}).get('queues', "active, deferred, hold, incoming").split(',')))

        top_domains = frozenset(map(strip, self.config.get('postfix', {}).get('top_domains', "").split(',')))

        data = {'global':{}, 'domains':{}}

        all_domains = {}

        for queue in queues:
            queue_stats = self.get_queue_stats(queue)

            data['global'].update({queue: queue_stats.pop('TOTAL')})

            for domain, stats in queue_stats.iteritems():
                all_domains.setdefault(domain, {}).update({queue: stats})

                if domain in top_domains:
                     data['domains'].setdefault(domain, {}).update({queue: stats})

        data['all_domains'] = flatten(all_domains, ";:|?,=")

        return data

