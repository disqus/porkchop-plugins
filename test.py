from porkchop.plugin import PorkchopPlugin

class TestPlugin(PorkchopPlugin):
  def __init__(self):
    self.refresh = 5

  def get_data(self):
    return {'fred': 'wilma', 'barney': 'betty'}
