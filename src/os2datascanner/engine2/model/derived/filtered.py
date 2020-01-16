import os.path
from abc import abstractmethod
from bz2 import BZ2File
from gzip import GzipFile
from lzma import LZMAFile
from datetime import datetime
from functools import partial
from contextlib import contextmanager

from ...rules.types import InputType
from ..core import (Source,
        Handle, FileResource, SourceManager, ResourceUnavailableError)
from ..utilities import MultipleResults, NamedTemporaryResource
from .derived import DerivedSource


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
        yield self.handle.follow(sm)

    def censor(self):
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
        self._mr = None

    def _poke_stream(self, s):
        """Peeks at a single byte from the compressed stream, in the process
        both checking that it's valid and populating header values."""
        try:
            s.peek(1)
            return s
        except (OSError, EOFError) as ex:
            raise ResourceUnavailableError(self.handle, *ex.args)

    def unpack_stream(self):
        if not self._mr:
            with self.make_stream() as s:
                # Compute the size by seeking to the end of a fresh stream, in
                # the process also populating the last modification date field
                s.seek(0, 2)
                self._mr = MultipleResults.make_from_attrs(s,
                        "mtime", "filename", size=s.tell())
                self._mr[InputType.LastModified] = datetime.fromtimestamp(
                        s.mtime)
        return self._mr

    def get_size(self):
        return self.unpack_stream()["size"]

    def get_last_modified(self):
        return self.unpack_stream().setdefault(InputType.LastModified,
                super().get_last_modified())

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
                    # Poke the stream to make sure that it's valid
                    s.peek(1)
                    yield s
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
        return FilteredHandle(self.source.censor(), self.relative_path)
