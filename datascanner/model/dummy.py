from .core import Source, Handle, Resource

class DummySource(Source):
    def __init__(self, *handles):
        self._handles = handles

    def handles(self, sm):
        for h in self._handles:
            yield h
