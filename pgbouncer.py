import glob
import psycopg2
import psycopg2.extras
import re

from porkchop.plugin import PorkchopPlugin

def exc(conn, query, col_key = None, col_val = None):
  data = {}
  cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
  cursor.execute(query)

  if col_key and col_val:
    for row in cursor.fetchall():
      data[row[col_key]] = row[col_val]
  else:
    data = cursor.fetchall()

  return data

class PgbouncerPlugin(PorkchopPlugin):
  def _connect(self, **kwargs):
    host = kwargs.get('host', 'localhost')
    port = kwargs.get('port', '6432')
    user = kwargs.get('user', 'psql')
    password = kwargs.get('password', '')

    try:
      conn_string = "host='%s' port='%s' dbname='pgbouncer' user='%s'\
                    password='%s'" % (host, port, user, password)

      conn = psycopg2.connect(conn_string)
      conn.set_isolation_level(0) # don't need transactions
    except:
      return None

    return conn

  def get_data(self):
    data = self.gendict()

    instances = self._get_instances()

    for instance in instances.keys():
      # haven't decided how to best handle auth
      try:
        conn = self._connect(host=instances[instance]['addr'],
                             port=instances[instance]['port'])
        data[instance] = self._instance_stats(conn)
      except:
        pass

    return data

  def _get_instances(self):
    configs = glob.glob('/etc/pgbouncer/*.ini')
    r1 = re.compile('^listen_(addr|port)\s+=\s+(.*)$')
    instances = self.gendict()

    for file in configs:
      inst = file.split('/')[3].split('.')[0]

      with open(file, 'r') as f:
        for line in f:
          match = r1.match(line)
          if match:
            instances[inst].update({match.group(1): match.group(2)})

    return instances

  def _instance_stats(self, conn):
    data = self.gendict()

    for row in exc(conn, 'show stats'):
      for col in [key for key in row.keys() if key != 'database']:
        data[row['database']][col] = row[col]

    res = exc(conn, 'show servers')
    for x in xrange(len(res)):
      for col in [key for key in res[x].keys()]:
        data['server%d' % x][col] = res[x][col]

    res = exc(conn, 'show clients')
    for x in xrange(len(res)):
      for col in [key for key in res[x].keys()]:
        data['client%d' % x][col] = res[x][col]

    for row in exc(conn, 'show pools'):
      for col in [key for key in row.keys() if key != 'database']:
        data[row['database']][col] = row[col]

    data['lists'] = exc(conn, 'show lists', 'list', 'items')

    for row in exc(conn, 'show databases'):
      for col in [key for key in row.keys() if key != 'name']:
        data[row['database']][col] = row[col]

    for row in exc(conn, 'show fds'):
      for col in [key for key in row.keys() if key != 'fd']:
        data['fd%d' % row['fd']][col] = row[col]

    return data
