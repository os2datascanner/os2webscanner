from tarfile import open as open_tar
from datetime import datetime
from contextlib import contextmanager

from ...rules.types import InputType
from ..core import Source, Handle, FileResource, SourceManager
from ..utilities import MultipleResults, NamedTemporaryResource
from .derived import DerivedSource


@Source.mime_handler("application/x-tar")
class TarSource(DerivedSource):
    type_label = "tar"

    def handles(self, sm):
        tarfile = sm.open(self)
        for f in tarfile.getmembers():
            if f.isfile():
                yield TarHandle(self, f.name)

    def _generate_state(self, sm):
        with self.handle.follow(sm).make_path() as r:
            with open_tar(str(r), "r") as tp:
                yield tp


class TarResource(FileResource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._mr = None

    def unpack_info(self):
        if not self._mr:
            self._mr = MultipleResults.make_from_attrs(
                    self._get_cookie().getmember(self.handle.relative_path),
                    "chksum", "devmajor", "devminor", "gid", "gname",
                    "linkname", "linkpath", "mode", "mtime", "name", "offset",
                    "offset_data", "path", "pax_headers", "size", "sparse",
                    "tarfile", "type", "uid", "uname")
            self._mr[InputType.LastModified] = datetime.fromtimestamp(
                    self._mr["mtime"].value)
        return self._mr

    def get_size(self):
        return self.unpack_info()["size"]

    def get_last_modified(self):
        return self.unpack_info().setdefault(InputType.LastModified,
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
        return TarHandle(self.source.censor(), self.relative_path)
