from porkchop.plugin import PorkchopPlugin


class TestPlugin(PorkchopPlugin):
    def __init__(self, *args, **kwargs):
        self.refresh = 5
        super(TestPlugin, self).__init__(*args, **kwargs)

    def get_data(self):
        return {'fred': 'wilma', 'barney': 'betty'}
