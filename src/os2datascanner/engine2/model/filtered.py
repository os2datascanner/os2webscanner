from .core import Source, Handle, FileResource
from .utilities import NamedTemporaryResource

import os.path
from bz2 import BZ2File
from enum import Enum
from gzip import GzipFile
from lzma import LZMAFile
from hashlib import md5
from functools import partial
from contextlib import contextmanager

class FilterType(Enum):
    GZIP = "gzip"
    BZ2 = "bz2"
    LZMA = "lzma"

class FilteredSource(Source):
    eq_properties = ("_handle", "_filter_type")
    type_label = "filtered"

    def __init__(self, handle, filter_type):
        self._handle = handle
        self._filter_type = filter_type

        # Both BZ2File and LZMAFile accept either a file name or a file object
        # as their first parameter, but GzipFile requires that we specify the
        # fileobj positional parameter instead
        if self._filter_type == FilterType.GZIP:
            self._constructor = (
                    lambda stream: GzipFile(fileobj=stream, mode='r'))
        elif self._filter_type == FilterType.BZ2:
            self._constructor = partial(BZ2File, mode='r')
        elif self._filter_type == FilterType.LZMA:
            self._constructor = partial(LZMAFile, mode='r')
        else:
            raise ValueError(self._filter_type)

    def __str__(self):
        return "FilteredSource({0})".format(self._handle)

    def handles(self, sm):
        rest, ext = os.path.splitext(self._handle.get_name())
        yield FilteredHandle(self, rest)

    def _generate_state(self, sm):
        yield self._handle.follow(sm)

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "handle": self._handle.to_json_object(),
            "filter_type": self._filter_type.value
        })

    @staticmethod
    @Source.json_handler(type_label)
    def from_json_object(obj):
        return FilteredSource(
                handle=Handle.from_json_object(obj["handle"]),
                filter_type=FilterType(obj["filter_type"]))

@Source.mime_handler("application/gzip")
def _gzip(handle):
    return FilteredSource(handle, FilterType.GZIP)

@Source.mime_handler("application/x-bzip2")
def _bz2(handle):
    return FilteredSource(handle, FilterType.BZ2)

@Source.mime_handler("application/x-xz")
def _lzma(handle):
    return FilteredSource(handle, FilterType.LZMA)

class FilteredHandle(Handle):
    type_label = "filtered"

    def follow(self, sm):
        return FilteredResource(self, sm)
Handle.stock_json_handler(FilteredHandle.type_label, FilteredHandle)

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
        with self._get_cookie().make_stream() as s_:
            with self.get_handle().get_source()._constructor(s_) as s:
                yield s
