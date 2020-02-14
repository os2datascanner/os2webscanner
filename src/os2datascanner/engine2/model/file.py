from .core import Source, Handle, FileResource

from os import stat
import os.path
from urllib.parse import quote, unquote, urlsplit, urlunsplit
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager

from ..conversions.types import OutputType
from ..conversions.utilities.results import MultipleResults


class FilesystemSource(Source):
    type_label = "file"

    def __init__(self, path):
        if not os.path.isabs(path):
            raise ValueError("Path {0} is not absolute".format(path))
        self._path = path

    @property
    def path(self):
        return self._path

    def handles(self, sm):
        pathlib_path = Path(self.path)
        for d in pathlib_path.glob("**"):
            for f in d.iterdir():
                if f.is_file():
                    yield FilesystemHandle(self,
                            str(f.relative_to(pathlib_path)))

    def _generate_state(self, sm):
        """Yields a path to the directory against which relative paths should
        be resolved.

        Other classes can also produce FilesystemResources if they have a
        compatible implementation of this function."""
        yield self.path

    def censor(self):
        return self

    def to_url(self):
        return urlunsplit(('file', '', quote(str(self.path)), None, None))

    @staticmethod
    @Source.url_handler("file")
    def from_url(url):
        scheme, netloc, path, _, _ = urlsplit(url)
        assert not netloc
        return FilesystemSource(unquote(path) if path else None)

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "path": self.path
        })

    @staticmethod
    @Source.json_handler(type_label)
    def from_json_object(obj):
        return FilesystemSource(path=obj["path"])


stat_attributes = ("st_mode", "st_ino", "st_dev", "st_nlink", "st_uid",
        "st_gid", "st_size", "st_atime", "st_mtime", "st_ctime",
        "st_blksize", "st_blocks", "st_rdev", "st_flags",)


class FilesystemResource(FileResource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._full_path = os.path.join(
                self._get_cookie(), self.handle.relative_path)
        self._mr = None

    def unpack_stat(self):
        if not self._mr:
            self._mr = MultipleResults.make_from_attrs(
                    os.stat(self._full_path), *stat_attributes)
            self._mr[OutputType.LastModified] = datetime.fromtimestamp(
                    self._mr["st_mtime"].value)
        return self._mr

    def get_size(self):
        return self.unpack_stat()["st_size"]

    def get_last_modified(self):
        return self.unpack_stat().setdefault(
                OutputType.LastModified, super().get_last_modified())

    @contextmanager
    def make_path(self):
        yield self._full_path

    @contextmanager
    def make_stream(self):
        with open(self._full_path, "rb") as s:
            yield s


@Handle.stock_json_handler("file")
class FilesystemHandle(Handle):
    type_label = "file"
    resource_type = FilesystemResource

    @property
    def presentation(self):
        return str(Path(self.source.path).joinpath(self.relative_path))

    def censor(self):
        return FilesystemHandle(self.source.censor(), self.relative_path)

    @classmethod
    def make_handle(cls, path):
        """Given a local filesystem path, returns a FilesystemHandle pointing
        at it."""
        head, tail = os.path.split(path)
        if not tail:
            raise ValueError("FilesystemHandles must have a non-empty Path")
        return FilesystemHandle(FilesystemSource(head), tail)
