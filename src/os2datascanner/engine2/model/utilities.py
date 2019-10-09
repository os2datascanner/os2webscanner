from os import rmdir, remove
from pathlib import Path
from tempfile import mkdtemp

class NamedTemporaryResource:
    def __init__(self, name):
        self._name = name
        self._dir = None

    def open(self, mode):
        if self._dir is None:
            self._dir = Path(mkdtemp())
        try:
            return self.get_path().open(mode)
        except:
            raise

    def get_path(self) -> Path:
        return self._dir.joinpath(self._name)

    def finished(self):
        self.get_path().unlink()
        self._dir.rmdir()
        self._dir = None

