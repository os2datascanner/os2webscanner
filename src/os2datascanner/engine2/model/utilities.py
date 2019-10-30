from os import rmdir, remove
import os.path
from tempfile import mkdtemp

class NamedTemporaryResource:
    def __init__(self, name):
        self._name = name
        self._dir = None

    def open(self, mode):
        if self._dir is None:
            self._dir = mkdtemp()
        return open(self.get_path(), mode)

    def get_path(self) -> str:
        return os.path.join(self._dir, self._name)

    def finished(self):
        remove(self.get_path())
        rmdir(self._dir)
        self._dir = None
