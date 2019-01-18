from model.core import Source, Handle, Resource
from model.utilities import NamedTemporaryResource

from pathlib import Path
from zipfile import ZipFile
from datetime import datetime

class ZipSource(Source):
    def __init__(self, handle):
        self._handle = handle
        self._zip = None

    def __str__(self):
        return "ZipSource({0})".format(self._handle)

    def files(self, sm):
        _, zipfile = sm.open(self)
        for f in zipfile.namelist():
            if not f[-1] == "/":
                yield ZipHandle(self, f)

    def _open(self, sm):
        r = self._handle.follow(sm)
        path = r.__enter__()
        return (r, ZipFile(path))

    def _close(self, cookie):
        r, zipfile = cookie
        r.__exit__(None, None, None)
        zipfile.close()

class ZipHandle(Handle):
    def __init__(self, source, relpath):
        super(ZipHandle, self).__init__(source, Path(relpath))

    def follow(self, sm):
        return ZipResource(self, sm)

class ZipResource(Resource):
    def __init__(self, handle, sm):
        super(ZipResource, self).__init__(handle, sm)
        self._info = None
        self._ntr = None

    def get_info(self):
        if not self._info:
            self._info = self.open()[1].getinfo(str(self._handle.get_relative_path()))
        return self._info

    def get_hash(self):
        return self.get_info().CRC

    def get_last_modified(self):
        return datetime(*self.get_info().date_time)

    def __enter__(self):
        assert not self._ntr
        self._ntr = NamedTemporaryResource(Path(self._handle.get_name()))
        with self._ntr.open("wb") as f:
            with self.open()[1].open(str(self._handle.get_relative_path())) as res:
                f.write(res.read())
        return self._ntr.get_path()

    def __exit__(self, exc_type, exc_value, traceback):
        assert self._ntr
        self._ntr.finished()
        self._ntr = None
