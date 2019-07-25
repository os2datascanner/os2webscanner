from .core import Source, Handle, FileResource
from .utilities import NamedTemporaryResource

from bz2 import BZ2File
from gzip import GzipFile
from lzma import LZMAFile
from hashlib import md5
from pathlib import Path
from functools import partial
from contextlib import contextmanager

class FilteredSource(Source):
    def __init__(self, handle, constructor):
        self._handle = handle
        self._constructor = constructor

    def __str__(self):
        return "FilteredSource({0})".format(self._handle)

    def handles(self, sm):
        yield FilteredHandle(
                self, Path(self._handle.get_name()).with_suffix(""))

    def _open(self, sm):
        return self._handle.follow(sm)

    def _close(self, cookie):
        pass

@Source.mime_handler("application/gzip")
def _gzip(handle):
    # Both BZ2File and LZMAFile accept either a file name or a file object as
    # their first parameter, but GzipFile requires that we specify the fileobj
    # positional parameter instead
    return FilteredSource(handle,
            lambda stream: GzipFile(fileobj=stream, mode='r'))

@Source.mime_handler("application/x-bzip2")
def _bz2(handle):
    return FilteredSource(handle, partial(BZ2File, mode='r'))

@Source.mime_handler("application/x-xz")
def _lzma(handle):
    return FilteredSource(handle, partial(LZMAFile, mode='r'))

class FilteredHandle(Handle):
    def follow(self, sm):
        return FilteredResource(self, sm)

class FilteredResource(FileResource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._md5 = None

    def get_hash(self):
        if not self._md5:
            with self.make_stream() as s:
                self._md5 = md5(s.read())
        return self._md5

    def get_size(self):
        with self.make_stream() as s:
            initial = s.seek(0, 1)
            try:
                s.seek(0, 2)
                return s.tell()
            finally:
                s.seek(initial, 0)

    def get_last_modified(self):
        with self.make_stream() as s:
            return s.mtime

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
        with self._open_source().make_stream() as s_:
            with self.get_handle().get_source()._constructor(s_) as s:
                yield s
