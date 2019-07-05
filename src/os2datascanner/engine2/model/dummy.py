from .core import Source

class DummySource(Source):
    def __init__(self, *handles):
        self._handles = handles

    def handles(self, sm):
        for h in self._handles:
            yield h

    def _open(self, sm):
        pass

    def _close(self, cookie):
        pass
