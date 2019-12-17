from zipfile import ZipFile
from datetime import datetime
from contextlib import contextmanager

from ..rules.types import InputType
from .core import Source, Handle, FileResource, DerivedSource, SourceManager
from .utilities import MultipleResults, NamedTemporaryResource


@Source.mime_handler("application/zip")
class ZipSource(DerivedSource):
    type_label = "zip"

    def handles(self, sm):
        zipfile = sm.open(self)
        for f in zipfile.namelist():
            if not f[-1] == "/":
                yield ZipHandle(self, f)

    def _generate_state(self, sm):
        # Using a nested SourceManager means that closing this generator will
        # automatically clean up as much as possible
        with SourceManager(sm) as derived:
            with self.handle.follow(derived).make_path() as r:
                with ZipFile(str(r)) as zp:
                    yield zp


class ZipResource(FileResource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._mr = None

    def unpack_info(self):
        if not self._mr:
            self._mr = MultipleResults.make_from_attrs(
                    self._get_cookie().getinfo(str(self.handle.relative_path)),
                    "CRC", "comment", "compress_size", "compress_type",
                    "create_system", "create_version", "date_time",
                    "external_attr", "extra", "extract_version", "file_size",
                    "filename", "flag_bits", "header_offset", "internal_attr",
                    "orig_filename", "reserved", "volume")
            self._mr[InputType.LastModified] = datetime(
                    *self._mr["date_time"].value)
        return self._mr

    def get_size(self):
        return self.unpack_info()["file_size"]

    def get_last_modified(self):
        return self.unpack_info().get(InputType.LastModified,
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
        with self._get_cookie().open(self.handle.relative_path) as s:
            yield s


@Handle.stock_json_handler("zip")
class ZipHandle(Handle):
    type_label = "zip"
    resource_type = ZipResource

    @property
    def presentation(self):
        return "{0} (in {1})".format(
                self.relative_path, self.source.handle)

    def censor(self):
        return ZipHandle(self.source.censor(), self.relative_path)
