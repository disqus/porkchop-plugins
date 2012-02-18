import os.path
import re

from porkchop.plugin import PorkchopPlugin


def fmt(f):
    return '%.2f' % f


class DiskstatsPlugin(PorkchopPlugin):
    def get_data(self):
        script = '/proc/diskstats'

        if not os.path.exists(script):
            return {}

        data = {}

        stat_fields = [
            'rd',
            'rd_m',
            'rd_s',
            'rd_t',
            'wr',
            'wr_m',
            'wr_s',
            'wr_t',
            'running',
            'use',
            'aveq'
        ]

        r1 = re.compile('[a-z]d[a-z]$')
        with open(script, 'r') as f:
            for line in f:
                fields = line.strip().split()

                device = fields[2]
                fields = fields[3:]

                if not r1.match(device):
                    continue

                data.setdefault(device, {})

                for pos in xrange(len(fields)):
                    data[device][stat_fields[pos]] = float(fields[pos])

        return data

    def format_data(self, data):
        result = {}

        prev = self.prev_data

        for key in prev.keys():
            try:
                avg_req_sz = ((data[key]['rd_s'] - prev[key]['rd_s']) +\
                          (data[key]['wr_s'] - prev[key]['wr_s'])) /\
                         ((data[key]['rd'] + data[key]['wr']) -\
                          (prev[key]['rd'] + prev[key]['wr']))
            except ZeroDivisionError:
                avg_req_sz = 0

            try:
                avg_queue_sz = (data[key]['aveq'] - prev[key]['aveq']) / 1000
            except ZeroDivisionError:
                avg_queue_sz = 0

            try:
                avg_wait = ((data[key]['rd_t'] - prev[key]['rd_t']) +\
                        (data[key]['wr_t'] - prev[key]['wr_t'])) /\
                       ((data[key]['rd'] - prev[key]['rd']) +\
                        (data[key]['wr'] - prev[key]['wr']))
                avg_wait = avg_wait if avg_wait > 0 else 0
            except ZeroDivisionError:
                avg_wait = 0

            try:
                avg_read_wait = (data[key]['rd_t'] - prev[key]['rd_t']) /\
                            (data[key]['rd'] - prev[key]['rd'])
            except ZeroDivisionError:
                avg_read_wait = 0

            try:
                avg_write_wait = (data[key]['wr_t'] - prev[key]['wr_t']) /\
                             (data[key]['wr'] - prev[key]['wr'])
            except ZeroDivisionError:
                avg_write_wait = 0

            util = self.rateof(prev[key]['use'], data[key]['use'])

            try:
                svctime = util / self.rateof((prev[key]['rd'] + prev[key]['wr']),
                                 (data[key]['rd'] + data[key]['wr']))
            except ZeroDivisionError:
                svctime = 0

            result[key] = {
                'reads_per_second': fmt(self.rateof(prev[key]['rd'],
                                        data[key]['rd'])),
                'writes_per_second': fmt(self.rateof(prev[key]['wr'],
                                         data[key]['wr'])),
                'read_merges_per_second': fmt(self.rateof(prev[key]['rd_m'],
                                              data[key]['rd_m'])),
                'write_merges_per_second': fmt(self.rateof(prev[key]['wr_m'],
                                               data[key]['wr_m'])),
                'read_kilobytes_per_second': fmt(self.rateof(prev[key]['rd_s'],
                                                 data[key]['rd_s']) / 2),
                'write_kilobytes_per_second': fmt(self.rateof(prev[key]['wr_s'],
                                                  data[key]['wr_s']) / 2),
                'ios_in_progress': fmt(data[key]['running'] / self.delta),
                'average_request_size': fmt(avg_req_sz),
                'average_queue_size': fmt(avg_queue_sz / self.delta),
                'average_wait': fmt(avg_wait),
                'average_read_wait': fmt(avg_read_wait),
                'average_write_wait': fmt(avg_write_wait),
                'svctime': fmt(svctime),
                'util': fmt(util / 10)
            }

        return result
