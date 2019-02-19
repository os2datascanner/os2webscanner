from model.core import Source, Handle, Resource
from model.utilities import NamedTemporaryResource

from pathlib import Path
from zipfile import ZipFile
from datetime import datetime
from contextlib import contextmanager

class ZipSource(Source):
    def __init__(self, handle):
        self._handle = handle
        self._zip = None

    def __str__(self):
        return "ZipSource({0})".format(self._handle)

    def handles(self, sm):
        _, zipfile = sm.open(self)
        for f in zipfile.namelist():
            if not f[-1] == "/":
                yield ZipHandle(self, f)

    def _open(self, sm):
        r = self._handle.follow(sm).make_path()
        path = r.__enter__()
        return (r, ZipFile(path))

    def _close(self, cookie):
        r, zipfile = cookie
        r.__exit__(None, None, None)
        zipfile.close()

Source._register_mime_handler("application/zip", ZipSource)

class ZipHandle(Handle):
    def __init__(self, source, relpath):
        super(ZipHandle, self).__init__(source, Path(relpath))

    def follow(self, sm):
        return ZipResource(self, sm)

class ZipResource(Resource):
    def __init__(self, handle, sm):
        super(ZipResource, self).__init__(handle, sm)
        self._info = None

    def get_info(self):
        if not self._info:
            self._info = self._open_source()[1].getinfo(str(self._handle.get_relative_path()))
        return self._info

    def get_hash(self):
        return self.get_info().CRC

    def get_last_modified(self):
        return datetime(*self.get_info().date_time)

    @contextmanager
    def make_path(self):
        ntr = NamedTemporaryResource(Path(self._handle.get_name()))
        try:
            with ntr.open("wb") as f:
                with self.make_stream() as s:
                    f.write(s.read())
            yield ntr.get_path()
        finally:
            ntr.finished()

    @contextmanager
    def make_stream(self):
        with self._open_source()[1].open(str(self._handle.get_relative_path())) as s:
            yield s
