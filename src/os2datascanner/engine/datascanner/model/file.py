from .core import Source, Handle, FileResource, ShareableCookie

from urllib.parse import quote, unquote, urlsplit, urlunsplit
from hashlib import md5
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager

class FilesystemSource(Source):
    def __init__(self, path):
        self._path = Path(path)
        assert self._path.is_absolute()

    def handles(self, sm):
        for d in self._path.glob("**"):
            for f in d.iterdir():
                if f.is_file():
                    yield FilesystemHandle(self, f.relative_to(self._path))

    def __str__(self):
        return "FilesystemSource({0})".format(self._path)

    def _open(self, sm):
        return ShareableCookie(self._path)

    def _close(self, sm):
        pass

    def to_url(self):
        return urlunsplit(('file', '', quote(str(self._path)), None, None))

    @staticmethod
    @Source.url_handler("file")
    def from_url(url):
        scheme, netloc, path, _, _ = urlsplit(url)
        assert not netloc
        return FilesystemSource(unquote(path) if path else None)

class FilesystemHandle(Handle):
    def follow(self, sm):
        return FilesystemResource(self, sm)

class FilesystemResource(FileResource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._full_path = self._open_source().joinpath(
                self.get_handle().get_relative_path())
        self._hash = None
        self._stat = None

    def get_hash(self):
        if not self._hash:
            with self.make_stream() as f:
                self._hash = md5(f.read())
        return self._hash

    def get_stat(self):
        if not self._stat:
            self._stat = self._full_path.stat()
        return self._stat

    def get_last_modified(self):
        return datetime.fromtimestamp(self.get_stat().st_mtime)

    @contextmanager
    def make_path(self):
        yield str(self._full_path)

    @contextmanager
    def make_stream(self):
        with open(str(self._full_path), "rb") as s:
            yield s
