from .core import Source, Handle, FileResource, DerivedSource, SourceManager
from .utilities import NamedTemporaryResource

from zipfile import ZipFile
from datetime import datetime
from contextlib import contextmanager


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

    def _censor(self):
        return ZipSource(self.handle.censor())

    @staticmethod
    @Source.json_handler(type_label)
    def from_json_object(obj):
        return ZipSource(Handle.from_json_object(obj["handle"]))


@Handle.stock_json_handler("zip")
class ZipHandle(Handle):
    type_label = "zip"

    @property
    def presentation(self):
        return "{0} (in {1})".format(
                self.relative_path, self.source.handle)

    def censor(self):
        return ZipHandle(self.source._censor(), self.relative_path)

    def follow(self, sm):
        return ZipResource(self, sm)


class ZipResource(FileResource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._info = None

    def get_info(self):
        if not self._info:
            self._info = self._get_cookie().getinfo(
                    str(self.handle.relative_path))
        return self._info

    def get_size(self):
        return self.get_info().file_size

    def get_last_modified(self):
        return datetime(*self.get_info().date_time)

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
