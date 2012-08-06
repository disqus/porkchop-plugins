from collections import defaultdict
from subprocess import Popen, PIPE
from porkchop.plugin import PorkchopPlugin

class dotDict(defaultdict):
    def __init__(self):
        defaultdict.__init__(self, dotDict)
    def __setitem__(self, key, value):
        keys = key.split('.')
        for key in keys[:-1]:
            self = self[key]
        defaultdict.__setitem__(self, keys[-1], value)

class UnboundPlugin(PorkchopPlugin):
    def get_data(self):
        raw_stats = Popen("/usr/sbin/unbound-control stats", stdout=PIPE, shell=True).communicate()[0].splitlines()

        stats = dotDict()

        raw_histogram = {}

        for line in raw_stats:
            stat_name, stat_value = line.split('=')

            if not stat_name.startswith('histogram'):
                stats[stat_name] = stat_value
            else:
                hist_intv = float(stat_name.split('.', 4)[4])
                raw_histogram[hist_intv] = float(stat_value)

        histogram = defaultdict(int)

        for intv in sorted(raw_histogram.keys()):
            if intv <= 0.001024:
                # Let's compress <1ms into 1 data point
                histogram['1ms'] += raw_histogram[intv]
            elif intv < 1.0:
                # Convert to ms and since we're using the upper limit, divide by 2 for lower limit
                intv_name = ''.join([str(int(intv/0.001024/2)), 'ms+'])
                histogram[intv_name] = raw_histogram[intv]
            elif intv == 1.0:
                histogram['512ms+'] = raw_histogram[intv]
            elif intv > 1.0 and intv <= 64.0:
                # Convert upper limit into lower limit seconds
                intv_name = ''.join([str(int(intv/2)), 's+'])
                histogram[intv_name] = raw_histogram[intv]
            else:
                # Compress everything >64s into 1 data point
                histogram['64s+'] += raw_histogram[intv]

        stats['histogram'] = histogram

        return stats

