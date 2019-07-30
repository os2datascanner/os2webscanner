from .core import Source, Handle, FileResource
from .utilities import NamedTemporaryResource

from tarfile import open as open_tar
from datetime import datetime
from contextlib import contextmanager

@Source.mime_handler("application/x-tar")
class TarSource(Source):
    def __init__(self, handle):
        self._handle = handle

    def __str__(self):
        return "TarSource({0})".format(self._handle)

    def handles(self, sm):
        _, tarfile = sm.open(self)
        for f in tarfile.getmembers():
            if f.isfile():
                yield TarHandle(self, f.name)

    def _open(self, sm):
        r = self._handle.follow(sm).make_path()
        path = r.__enter__()
        return (r, open_tar(path, "r"))

    def _close(self, cookie):
        r, tarfile = cookie
        r.__exit__(None, None, None)
        tarfile.close()

class TarHandle(Handle):
    def follow(self, sm):
        return TarResource(self, sm)

class TarResource(FileResource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._info = None

    def get_info(self):
        if not self._info:
            self._info = self._open_source()[1].gettarinfo(
                    self.get_handle().get_relative_path())
        return self._info

    def get_hash(self):
        return self.get_info().chksum

    def get_size(self):
        return self.get_info().size

    def get_last_modified(self):
        return datetime(*self.get_info().mtime)

    @contextmanager
    def make_path(self):
        ntr = NamedTemporaryResource(Path(self.get_handle().get_name()))
        try:
            with ntr.open("wb") as f:
                with self.make_stream() as s:
                    f.write(s.read())
            yield ntr.get_path()
        finally:
            ntr.finished()

    @contextmanager
    def make_stream(self):
        with self._open_source()[1].extractfile(
                 self.get_handle().get_relative_path()) as s:
            yield s

