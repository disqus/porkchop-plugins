from subprocess import Popen, PIPE

from porkchop.plugin import PorkchopPlugin

class CassandraPlugin(PorkchopPlugin):

    # Get thread pool statistics
    @staticmethod
    def tp_data(self):
        data = self.gendict()

        # Prints usage statistics of thread pools
        cmd = ['/usr/bin/nodetool', 'tpstats']
        output = Popen(cmd, stdout=PIPE).communicate()[0].splitlines()

        # Normalize the metric names
        normalized = {
            'ReadStage': 'read_stage',
            'RequestResponseStage': 'request_response_stage',
            'MutationStage': 'mutation_stage',
            'ReadRepairStage': 'read_repair_stage',
            'ReplicateOnWriteStage': 'replicate_on_write_stage',
            'GossipStage': 'gossip_stage',
            'AntiEntropyStage': 'antientropy_stage',
            'MigrationStage': 'migration_stage',
            'MemtablePostFlusher': 'memtable_post_flusher',
            'StreamStage': 'stream_stage',
            'FlushWriter': 'flush_writer',
            'MiscStage': 'misc_stage',
            'commitlog_archiver': 'commitlog_archiver',
            'InternalResponseStage': 'internal_response_stage',
            'HintedHandoff': 'hinted_handoff'
        }

        # Starting text of output lines to skip
        skip_lines = [
            'Pool',
            'Message',
            'RANGE_SLICE',
            'READ_REPAIR',
            'BINARY',
            'READ',
            'MUTATION',
            'REQUEST_RESPONSE'
        ]

        # Number of threads in each state
        state_counts = { 
            'active': 1, 
            'pending': 2, 
            'completed': 3, 
            'blocked': 4, 
            'all_time_blocked': 5
        } 

        # Examine the output of nodetool
        for line in output:
            # Skip lines without any data
            if not line.strip() or line.split()[0] in skip_lines:
                continue
            # Parse lines with data
            else:
                contents = line.split()
                key = contents[0]

                # Extract the count of threads in each state and normalize
                if key in normalized.keys():
                    for state, index in state_counts.items():
                        data["tpstats"][normalized[key]][state] = contents[index]
                else:
                    continue

        return data

    # Get column family statistics 
    @staticmethod
    def cf_data(self):
        data = self.gendict()

        # Prints statistics on column families
        cmd = ['/usr/bin/nodetool', 'cfstats']
        output = Popen(cmd, stdout=PIPE).communicate()[0].splitlines()

        # Start with no known keyspace and column family names  
           keyspace = ""
        cf = ""
    
        # Normalize the metric names
        normalized = {
            'SSTable count': 'sstable_count',
            'Space used (live)': 'space_used_live',
            'Space used (total)': 'space_used_total',
            'Number of Keys (estimate)': 'num_key_est',
            'Memtable Columns Count': 'memtable_count',
            'Memtable Data Size': 'memtable_data_size',
            'Memtable Switch Count': 'memtable_switch_count',
            'Read Count': 'read_count',
            'Read Latency': 'read_latency',
            'Write Count': 'write_count',
            'Write Latency': 'write_latency',
            'Pending Tasks': 'pending_tasks',
            'Bloom Filter False Postives': 'bloom_filter_false_positives',
            'Bloom Filter False Ratio': 'bloom_filter_false_ratio',
            'Bloom Filter Space Used': 'bloom_filter_space_used',
            'Compacted row minimum size': 'compacted_row_min_size',
            'Compacted row maximum size': 'compacted_row_max_size',
            'Compacted row mean size': 'compacted_row_mean_size'
          }

        # Examine the output of nodetool
        for line in output:
            # Skip lines without any data
            if not line.strip() or "----------------" in line:
                continue
            # We have found a new keyspace
            elif line.startswith('Keyspace'):
                parts = line.split(":")
                keyspace = parts[1].strip().lower()
                cf = ""
            # We have a found a new column family
            elif "Family" in line:
                parts = line.split(":")
                cf = parts[1].strip().lower()
            # Grab the data for this keyspace / column family combo
        elif cf != "":
                key, val = line.split(":")
                if val == "NaN":
                    val = "0.0"
                val = float(val.split()[0])
                key = key.strip()

                if key in normalized.keys():
                    data["cfstats"][keyspace][cf][normalized[key]] = val
                else:
                    continue

        return data

    def get_data(self):
        data = {}
        data.update(self.cf_data(self))
        data.update(self.tp_data(self))
        return data
