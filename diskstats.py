import os
import re
import time

from porkchop.plugin import PorkchopPlugin

def fmt(f):
  return '%.2f' % f


def read_info():
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
  with open('/proc/diskstats', 'r') as f:
    for line in f:
      fields = line.strip().split()
      fields.pop(0); fields.pop(0)
      device = fields[0]
      fields.pop(0)

      if not r1.match(device): continue

      data.setdefault(device, {})

      for pos in xrange(len(fields)):
        data[device][stat_fields[pos]] = float(fields[pos])

  return data

class DiskstatsPlugin(PorkchopPlugin):
  def get_data(self):
    data = {}

    if not self.__class__._cache:
      prev = read_info()
      delta = 1
      time.sleep(delta)
    else:
      prev = self.__class__._cache
      delta = int(time.time() - self.__class__._lastrefresh)

    self.__class__._cache = cur = read_info()

    for key in prev.keys():
      try:
        avg_req_sz = ((cur[key]['rd_s'] - prev[key]['rd_s']) +\
                      (cur[key]['wr_s'] - prev[key]['wr_s'])) /\
                     ((cur[key]['rd'] + cur[key]['wr']) -\
                      (prev[key]['rd'] + prev[key]['wr']))
      except ZeroDivisionError:
        avg_req_sz = 0

      try:
        avg_queue_sz = (cur[key]['aveq'] - prev[key]['aveq']) / 1000
      except ZeroDivisionError:
        avg_queue_sz = 0

      try:
        avg_wait = ((cur[key]['rd_t'] - prev[key]['rd_t']) +\
                    (cur[key]['wr_t'] - prev[key]['wr_t'])) /\
                   ((cur[key]['rd'] - prev[key]['rd']) +\
                    (cur[key]['wr'] - prev[key]['wr']))
        avg_wait = avg_wait if avg_wait > 0 else 0
      except ZeroDivisionError:
        avg_wait = 0

      try:
        avg_read_wait = (cur[key]['rd_t'] - prev[key]['rd_t']) /\
                        (cur[key]['rd'] - prev[key]['rd'])
      except ZeroDivisionError:
        avg_read_wait = 0

      try:
        avg_write_wait = (cur[key]['wr_t'] - prev[key]['wr_t']) /\
                         (cur[key]['wr'] - prev[key]['wr'])
      except ZeroDivisionError:
        avg_write_wait = 0

      util = self.rateof(prev[key]['use'], cur[key]['use'], delta)

      try:
        svctime = util / self.rateof((prev[key]['rd'] + prev[key]['wr']),
                             (cur[key]['rd'] + cur[key]['wr']), delta)
      except ZeroDivisionError:
        svctime = 0

      data[key] = {
        'reads_per_second': fmt(self.rateof(prev[key]['rd'],
                                cur[key]['rd'], delta)),
        'writes_per_second': fmt(self.rateof(prev[key]['wr'],
                                 cur[key]['wr'], delta)),
        'read_merges_per_second': fmt(self.rateof(prev[key]['rd_m'],
                                      cur[key]['rd_m'], delta)),
        'write_merges_per_second': fmt(self.rateof(prev[key]['wr_m'],
                                       cur[key]['wr_m'], delta)),
        'read_kilobytes_per_second': fmt(self.rateof(prev[key]['rd_s'],
                                         cur[key]['rd_s'], delta) / 2),
        'write_kilobytes_per_second': fmt(self.rateof(prev[key]['wr_s'],
                                          cur[key]['wr_s'], delta) / 2),
        'ios_in_progress': fmt(cur[key]['running'] / delta),
        'average_request_size': fmt(avg_req_sz),
        'average_queue_size': fmt(avg_queue_sz / delta),
        'average_wait': fmt(avg_wait),
        'averate_read_wait': fmt(avg_read_wait),
        'averate_write_wait': fmt(avg_write_wait),
        'svctime': fmt(svctime),
        'util': fmt(util / 10)
      }

    return data
