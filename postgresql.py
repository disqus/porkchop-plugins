import copy
import psycopg2
import psycopg2.extras

from porkchop.plugin import PorkchopPlugin


def fmt(f):
    return '%.2f' % f


def exc(conn, query, col_key=None, col_val=None):
    data = {}
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(query)

    if col_key and col_val:
        for row in cursor.fetchall():
            data[row[col_key]] = row[col_val]
    else:
        data = cursor.fetchall()

    return data


class PostgresqlPlugin(PorkchopPlugin):
    def _connect(self, dbname=None):
        dbname = dbname if dbname else 'postgres'
        try:
            conn_string = "host='%s' dbname='%s' user='%s' password='%s'" % (
                self.config['postgresql']['host'],
                dbname,
                self.config['postgresql']['user'],
                self.config['postgresql']['password'],
            )
            conn = psycopg2.connect(conn_string)
            conn.set_isolation_level(0)  # don't need transactions
        except Exception, e:
            self.log_error('Unable to connect to database %s on %s: %s' % (
                dbname,
                self.config['postgresql']['host'],
                e,
            ))
            return None
        return conn

    def get_data(self):
        data = self.gendict()
        conn = self._connect()
        if not conn:
            return {}

        all_conn_count_query = "SELECT tmp.state,COALESCE(count,0) FROM \
                               (VALUES ('active'),('waiting'),('idle'),\
                               ('idletransaction'),('unknown')) AS tmp(state) \
                               LEFT JOIN \
                               (SELECT CASE WHEN waiting THEN 'waiting' \
                                 WHEN current_query='<IDLE>' THEN 'idle' \
                                 WHEN current_query='<IDLE> in transaction' \
                                 THEN 'idletransaction' \
                                 WHEN current_query='<insufficient privilege>' \
                                 THEN 'unknown' ELSE 'active' END AS state, \
                                 count(*) AS count \
                                 FROM pg_stat_activity \
                                 WHERE procpid != pg_backend_pid() \
                                 GROUP BY CASE WHEN waiting THEN 'waiting' \
                                 WHEN current_query='<IDLE>' THEN 'idle' \
                                 WHEN current_query='<IDLE> in transaction' \
                                 THEN 'idletransaction' \
                                 WHEN current_query='<insufficient privilege>' \
                                 THEN 'unknown' ELSE 'active' END \
                               ) AS tmp2 \
                               ON tmp.state=tmp2.state ORDER BY 1"

        user_conn_count_query = 'SELECT usename,count(*) \
                                FROM pg_stat_activity \
                                WHERE procpid != pg_backend_pid() \
                                GROUP BY usename ORDER BY 1'
        locks_query = 'SELECT lower(mode) AS mode,count(*) \
                      FROM pg_locks WHERE database \
                      IS NOT NULL GROUP BY mode ORDER BY 1'
        db_size_query = 'SELECT datname,pg_database_size(oid) \
                         FROM pg_database ORDER BY 1'
        query_time_query = "SELECT 'query' AS type, COALESCE(max(extract(epoch \
                           FROM CURRENT_TIMESTAMP-query_start)),0) \
                           FROM pg_stat_activity WHERE current_query \
                           NOT LIKE '<IDLE%' UNION ALL \
                           SELECT 'transaction', \
                           COALESCE(max(extract(epoch \
                           FROM CURRENT_TIMESTAMP-xact_start)),0) \
                           FROM pg_stat_activity WHERE 1=1"
        idle_xact_time_query = "SELECT datname, \
                                max(COALESCE(ROUND(EXTRACT(epoch \
                                FROM now()-query_start)),0)) FROM pg_stat_activity \
                                WHERE current_query = '<IDLE> in transaction' \
                                GROUP BY 1"
        xact_count_query = "SELECT 'commit' AS type, \
                           sum(pg_stat_get_db_xact_commit(oid)) FROM pg_database \
                           UNION ALL SELECT 'rollback', \
                           sum(pg_stat_get_db_xact_rollback(oid)) FROM pg_database"
        scan_type_query = 'SELECT COALESCE(sum(seq_scan),0) AS sequential, \
                          COALESCE(sum(idx_scan),0) AS index \
                          FROM pg_stat_user_tables'
        tuple_access_query = "SELECT COALESCE(sum(seq_tup_read),0) AS seqread, \
                             COALESCE(sum(idx_tup_fetch),0) AS idxfetch, \
                             COALESCE(sum(n_tup_ins),0) AS inserted, \
                             COALESCE(sum(n_tup_upd),0) AS updated, \
                             COALESCE(sum(n_tup_del),0) AS deleted, \
                             COALESCE(sum(n_tup_hot_upd),0) AS hotupdated \
                             FROM pg_stat_user_tables"

        datnames = self._get_db_names(conn)
        data['datnames'] = ', '.join(datnames)

        data['query_time'] = exc(conn, query_time_query, 'type', 'coalesce')

        data['bgwrite'] = self._get_bgwriter_data(conn)
        data['buffercache'] = self._get_buffercache_data(conn)

        data['connections'] = {
            'state': exc(conn, all_conn_count_query, 'state', 'coalesce'),
            'database': self._count_num_dbs(conn),
            'user': exc(conn, user_conn_count_query, 'usename', 'count')
        }

        data['size'] = exc(conn, db_size_query, 'datname', 'pg_database_size')
        data['locks'] = exc(conn, locks_query, 'mode', 'count')
        data['idle_xact_time'] = exc(conn, idle_xact_time_query, 'datname', 'max')
        data['xactn_count'] = exc(conn, xact_count_query, 'type', 'sum')

        data['xlog'] = self._get_xlog_data(conn)

        for db in datnames:
            conn2 = self._connect(db)
            if conn2 is None:
                continue
            row = exc(conn2, tuple_access_query)[0]
            for key in row.iterkeys():
                data['tuple_access'][db][key] = row[key]

            row = exc(conn2, scan_type_query)[0]
            for key in row.iterkeys():
                data['scans'][db][key] = row[key]

            # Grab statistics per table
            data['table_stats'][db] = self._get_table_stats(conn2)

        try:
            slony_db = self.config['postgresql']['slony_db']
            slony_node_string = self.config['postgresql']['slony_node_string']
            slony_table = self.config['postgresql']['slony_table']

            replication_lag_query = "SELECT SUBSTRING(sl.no_comment \
                                  FROM '%s') AS NODE, \
                                  st.st_lag_num_events AS lag_events \
                                  FROM %s.sl_status AS st, %s.sl_node AS sl \
                                  WHERE sl.no_id = st.st_received" % \
                                  (slony_node_string, slony_table, slony_table)

            conn2 = self._connect(slony_db)
            data['slony_replication'] = exc(conn2, replication_lag_query, 'node', 'lag_events')
        except:
            pass

        return data

    def format_data(self, data):
        result = copy.deepcopy(data)

        # change tuple_stats to be rateof
        for db, db_data in data['tuple_access'].iteritems():
            for key, value in db_data.iteritems():
                prev_value = self.prev_data['tuple_stats'][db][key] or 0
                result['tuple_access'][db][key] = fmt(self.rateof(prev_value, value))

        # change table_stats to be rateof
        for db, db_data in data['table_stats'].iteritems():
            for schema_name, schema_data in db_data.iteritems():
                for table_name, table_data in schema_data.iteritems():
                    for key, value in table_data.iteritems():
                        prev_value = self.prev_data['table_stats'][db][schema_name][table_name][key] or 0
                        result['table_stats'][db][schema_name][table_name][key] = fmt(self.rateof(prev_value, value))
        return result

    def _get_bgwriter_data(self, conn):
        try:
            row = exc(conn, 'SELECT * from pg_stat_bgwriter')[0]
        except KeyError:
            return None

        result = {}
        for key in row.iterkeys():
            result[key] = row[key]
        return result

    def _get_buffercache_data(self, conn):
        query = """
            SELECT sum(blks_read)
            AS blks_read,sum(blks_hit) AS blks_hit
            FROM pg_stat_database
        """

        try:
            row = exc(conn, query)[0]
        except KeyError:
            return None

        result = {}
        for key in row.iterkeys():
            result[key] = row[key]

        return result

    def _get_xlog_data(self, conn):
        query = """
            SELECT count(*) AS segments FROM pg_ls_dir('pg_xlog') t(fn)
            WHERE fn ~ '^[0-9A-Z]{24}\$'
        """

        try:
            row = exc(conn, query)[0]
        except KeyError:
            return None

        result = {}
        for key in row.iterkeys():
            result[key] = row[key]
        return result

    def _get_db_names(self, conn):
        query = """
            SELECT datname FROM pg_database
            WHERE datallowconn AND NOT datistemplate
            AND NOT datname='postgres' ORDER BY 1
        """

        results = exc(conn, query)
        return [d[0] for d in results]

    def _get_table_stats(self, conn):
        query = """
            SELECT schemaname, relname,
            COALESCE(seq_tup_read,0) AS seqread,
            COALESCE(seq_scan,0) AS seqscan,
            COALESCE(idx_tup_fetch,0) AS idxfetch,
            COALESCE(idx_scan,0) AS idxscan,
            COALESCE(n_tup_ins,0) AS inserted,
            COALESCE(n_tup_upd,0) AS updated,
            COALESCE(n_tup_del,0) AS deleted,
            COALESCE(n_tup_hot_upd,0) AS hotupdated
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
        """

        data = {}
        results = exc(conn, query)
        for row in results:
            data.setdefault(row['schemaname'], {})
            row_result = data[row['schemaname']][row['relname']] = {}
            for key in (k for k in row.iterkeys() if k not in ('schemaname', 'relname')):
                row_result[key] = row[key]
        return data

    def _count_num_dbs(self, conn):
        query = """
            SELECT pg_database.datname,
            COALESCE(count,0) AS count FROM pg_database
            LEFT JOIN
            (SELECT datname,count(*) FROM pg_stat_activity
            WHERE procpid != pg_backend_pid()
            GROUP BY datname) AS tmp
            ON pg_database.datname=tmp.datname
            WHERE datallowconn ORDER BY 1
        """
        try:
            return exc(conn, query, 'datname', 'count')[0]
        except:
            return None
