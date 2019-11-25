from .core import Source, Handle, FileResource, SourceManager
from .utilities import NamedTemporaryResource

from tarfile import open as open_tar
from datetime import datetime
from contextlib import contextmanager


@Source.mime_handler("application/x-tar")
class TarSource(Source):
    type_label = "tar"

    def __init__(self, handle):
        self._handle = handle

    def __str__(self):
        return "TarSource({0})".format(self._handle)

    def handles(self, sm):
        tarfile = sm.open(self)
        for f in tarfile.getmembers():
            if f.isfile():
                yield TarHandle(self, f.name)

    def _generate_state(self, sm):
        # Using a nested SourceManager means that closing this generator will
        # automatically clean up as much as possible
        with SourceManager(sm) as derived:
            with self._handle.follow(derived).make_path() as r:
                with open_tar(str(r), "r") as tp:
                    yield tp

    def to_handle(self):
        return self._handle

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "handle": self._handle.to_json_object()
        })

    @staticmethod
    @Source.json_handler(type_label)
    def from_json_object(obj):
        return TarSource(Handle.from_json_object(obj["handle"]))


@Handle.stock_json_handler("tar")
class TarHandle(Handle):
    type_label = "tar"

    @property
    def presentation(self):
        return "{0} (in {1})".format(
                self.relative_path, self.source.to_handle())

    def follow(self, sm):
        return TarResource(self, sm)


class TarResource(FileResource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._info = None

    def get_info(self):
        if not self._info:
            self._info = self._get_cookie().getmember(
                    self.get_handle().relative_path)
        return self._info

    def get_size(self):
        return self.get_info().size

    def get_last_modified(self):
        return datetime.fromtimestamp(self.get_info().mtime)

    @contextmanager
    def make_path(self):
        ntr = NamedTemporaryResource(self.get_handle().name)
        try:
            with ntr.open("wb") as f:
                with self.make_stream() as s:
                    f.write(s.read())
            yield ntr.get_path()
        finally:
            ntr.finished()

    @contextmanager
    def make_stream(self):
        with self._get_cookie().extractfile(
                 self.get_handle().relative_path) as s:
            yield s
