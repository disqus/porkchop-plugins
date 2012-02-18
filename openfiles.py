import os.path

from porkchop.plugin import PorkchopPlugin


class OpenfilesPlugin(PorkchopPlugin):
    def get_data(self):
        script = '/proc/sys/fs/file-nr'
        if not os.path.exists(script):
            return {}

        with open(script, 'r') as f:
            fields = f.read().split()

            data = {
                'count': int(fields[0]) - int(fields[1]),
                'max': fields[2]
            }

        return data
