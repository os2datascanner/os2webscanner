from os import rmdir, remove
from pathlib import Path
from tempfile import mkdtemp

class NamedTemporaryResource:
    def __init__(self, name):
        self._name = name
        self._dir = None

    def open(self, mode):
        if not self._dir:
            self._dir = Path(mkdtemp())
        try:
            return open(self.get_path(), mode)
        except:
            raise

    def get_path(self):
        assert self._dir
        return self._dir.joinpath(self._name)

    def finished(self):
        assert self._dir
        remove(self.get_path())
        rmdir(self._dir)
        self._dir = None
