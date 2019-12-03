from .core import (Source, DerivedSource,
        Handle, FileResource, SourceManager, ResourceUnavailableError)
from .utilities import NamedTemporaryResource

import os.path
from bz2 import BZ2File
from enum import Enum
from gzip import GzipFile
from lzma import LZMAFile
from datetime import datetime
from functools import partial
from contextlib import contextmanager


class FilterType(Enum):
    GZIP = "gzip"
    BZ2 = "bz2"
    LZMA = "lzma"


class FilteredSource(DerivedSource):
    eq_properties = ("_handle", "_filter_type")
    type_label = "filtered"

    def __init__(self, handle, filter_type):
        super().__init__(handle)
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

    def handles(self, sm):
        rest, ext = os.path.splitext(self.handle.name)
        yield FilteredHandle(self, rest)

    def _generate_state(self, sm):
        # Using a nested SourceManager means that closing this generator will
        # automatically clean up as much as possible
        with SourceManager(sm) as derived:
            yield self.handle.follow(derived)

    def _censor(self):
        return FilteredSource(self.handle.censor(), self._filter_type)

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
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


class FilteredResource(FileResource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)

    def _poke_stream(self, s):
        """Peeks at a single byte from the compressed stream, in the process
        both checking that it's valid and populating header values."""
        try:
            s.peek(1)
            return s
        except (OSError, EOFError) as ex:
            raise ResourceUnavailableError(self.handle, *ex.args)

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
            # The mtime field won't have a meaningful value until the first
            # read operation has been performed, so read a single byte from
            # this new stream
            s.read(1)
            return datetime.fromtimestamp(s.mtime)

    @contextmanager
    def make_path(self):
        with NamedTemporaryResource(self.handle.name) as ntr:
            with ntr.open("wb") as f:
                with self.make_stream() as s:
                    f.write(s.read())
            yield ntr.get_path()

    @contextmanager
    def make_stream(self):
        with self._get_cookie().make_stream() as s_:
            try:
                with self.handle.source._constructor(s_) as s:
                    yield self._poke_stream(s)
            except OSError as ex:
                raise ResourceUnavailableError(self.handle, *ex.args)


@Handle.stock_json_handler("filtered")
class FilteredHandle(Handle):
    type_label = "filtered"
    resource_type = FilteredResource

    @property
    def presentation(self):
        return "({0}, decompressed)".format(
                self.source.handle.presentation)

    def censor(self):
        return FilteredHandle(self.source._censor(), self.relative_path)
