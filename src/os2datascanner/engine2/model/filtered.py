import os.path
from abc import abstractmethod
from bz2 import BZ2File
from gzip import GzipFile
from lzma import LZMAFile
from datetime import datetime
from functools import partial
from contextlib import contextmanager

from .core import (Source, DerivedSource,
        Handle, FileResource, SourceManager, ResourceUnavailableError)
from .utilities import NamedTemporaryResource


class FilteredSource(DerivedSource):
    def __init__(self, handle):
        super().__init__(handle)

    @classmethod
    @abstractmethod
    def _decompress(cls, stream):
        """Returns a Python file-like object that wraps the given compressed
        stream. Reading from this object will return decompressed content."""

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


@Source.mime_handler("application/gzip")
class GzipSource(FilteredSource):
    type_label = "filtered-gzip"

    @classmethod
    def _decompress(cls, stream):
        return GzipFile(fileobj=stream, mode="r")


@Source.mime_handler("application/x-bzip2")
class BZ2Source(FilteredSource):
    type_label = "filtered-bz2"

    @classmethod
    def _decompress(cls, stream):
        return BZ2File(stream, mode="r")


@Source.mime_handler("application/x-xz")
class LZMASource(FilteredSource):
    type_label = "filtered-lzma"

    @classmethod
    def _decompress(cls, stream):
        return LZMAFile(stream, mode="r")


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
                with self.handle.source._decompress(s_) as s:
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
