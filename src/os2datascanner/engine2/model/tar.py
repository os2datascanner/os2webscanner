from .core import Source, Handle, FileResource, DerivedSource, SourceManager
from .utilities import NamedTemporaryResource

from tarfile import open as open_tar
from datetime import datetime
from contextlib import contextmanager


@Source.mime_handler("application/x-tar")
class TarSource(DerivedSource):
    type_label = "tar"

    def handles(self, sm):
        tarfile = sm.open(self)
        for f in tarfile.getmembers():
            if f.isfile():
                yield TarHandle(self, f.name)

    def _generate_state(self, sm):
        # Using a nested SourceManager means that closing this generator will
        # automatically clean up as much as possible
        with SourceManager(sm) as derived:
            with self.handle.follow(derived).make_path() as r:
                with open_tar(str(r), "r") as tp:
                    yield tp


class TarResource(FileResource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._info = None

    def get_info(self):
        if not self._info:
            self._info = self._get_cookie().getmember(
                    self.handle.relative_path)
        return self._info

    def get_size(self):
        return self.get_info().size

    def get_last_modified(self):
        return datetime.fromtimestamp(self.get_info().mtime)

    @contextmanager
    def make_path(self):
        with NamedTemporaryResource(self.handle.name) as ntr:
            with ntr.open("wb") as f:
                with self.make_stream() as s:
                    f.write(s.read())
            yield ntr.get_path()

    @contextmanager
    def make_stream(self):
        with self._get_cookie().extractfile(self.handle.relative_path) as s:
            yield s


@Handle.stock_json_handler("tar")
class TarHandle(Handle):
    type_label = "tar"
    resource_type = TarResource

    @property
    def presentation(self):
        return "{0} (in {1})".format(
                self.relative_path, self.source.handle)

    def censor(self):
        return TarHandle(self.source._censor(), self.relative_path)
