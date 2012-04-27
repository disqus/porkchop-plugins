from porkchop.plugin import PorkchopPlugin


class TestPlugin(PorkchopPlugin):
    refresh = 5

    def __init__(self, *args, **kwargs):
        super(TestPlugin, self).__init__(*args, **kwargs)

    def get_data(self):
        return {'fred': 'wilma', 'barney': 'betty'}
