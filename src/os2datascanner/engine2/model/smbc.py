import structlog

from .smb import make_smb_url, SMBSource
from .core import Source, Handle, ShareableCookie, FileResource, ResourceUnavailableError
from .utilities import NamedTemporaryResource

from os import rmdir, stat_result, O_RDONLY
import smbc
from regex import compile, match
from urllib.parse import quote, unquote, urlsplit, urlunsplit
from datetime import datetime
from urllib.parse import quote
from contextlib import contextmanager


logger = structlog.get_logger()


class SMBCSource(Source):
    def __init__(self, unc, user=None, password=None, domain=None):
        self._unc = unc
        self._user = user
        self._password = password
        self._domain = domain

    def get_unc(self):
        return self._unc

    def __str__(self):
        return "SMBCSource({0}, {1}, ****, {2})".format(
                self._unc, self._user, self._domain)

    def _open(self, sm):
        context = smbc.Context()
        return (self._to_url(), context)

    def _close(self, cookie):
        # There seems to be no way to shut down a context
        pass

    def handles(self, sm):
        url, context = sm.open(self)
        def handle_dirent(parents, entity):
            here = parents + [entity]
            path = '/'.join([h.name for h in here])
            if entity.smbc_type == smbc.DIR and not (
                    entity.name == "." or entity.name == ".."):
                try:
                    obj = context.opendir(url + "/" + path)
                    for dent in obj.getdents():
                        yield from handle_dirent(here, dent)
                except ValueError:
                    pass
            elif entity.smbc_type == smbc.FILE:
                yield SMBCHandle(self, path)

        try:
            obj = context.opendir(url)
            for dent in obj.getdents():
                yield from handle_dirent([], dent)
        except Exception as exc:
            raise ResourceUnavailableError(self, *exc.args)

    def to_url(self):
        return make_smb_url(
                "smbc", self._unc, self._user, self._domain, self._password)

    # For our own purposes, we need to be able to make a "smb://" URL to give
    # to smbc
    def _to_url(self):
        return make_smb_url(
                "smb", self._unc, self._user, self._domain, self._password)

    @staticmethod
    @Source.url_handler("smbc")
    def from_url(url):
        scheme, netloc, path, _, _ = urlsplit(url)
        match = SMBSource.netloc_regex.match(netloc)
        if match:
            return SMBCSource("//" + match.group("unc") + unquote(path),
                match.group("username"), match.group("password"),
                match.group("domain"))
        else:
            return None

class SMBCHandle(Handle):
    def follow(self, sm):
        return SMBCResource(self, sm)

class SMBCResource(FileResource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._stat = None

    def open_file(self):
        try:
            url, context = self._open_source()
            my_url = url + "/" + quote(self.get_handle().get_relative_path())
            return context.open(my_url, O_RDONLY)
        except smbc.NoEntryError as ex:
            raise ResourceUnavailableError(self.get_handle(), ex)

    def get_stat(self):
        if not self._stat:
            f = self.open_file()
            try:
                self._stat = stat_result(f.fstat())
            finally:
                f.close()
        return self._stat

    def get_size(self):
        return self.get_stat().st_size

    def get_last_modified(self):
        return datetime.fromtimestamp(self.get_stat().st_mtime)

    # At the moment, we implement make_stream in terms of make_path: we
    # download the file's content in order to get a file-like object out of
    # it. We could, in theory, do this the other way round by implementing an
    # io.RawIOBase subclass that wraps smbc.File, but that seems more
    # complicated -- and, in early testing, actually had worse performance!

    @contextmanager
    def make_path(self):
        ntr = NamedTemporaryResource(self.get_handle().get_name())
        try:
            with ntr.open("wb") as f:
                rf = self.open_file()
                try:
                    buf = rf.read(self.DOWNLOAD_CHUNK_SIZE)
                    while buf:
                        f.write(buf)
                        buf = rf.read(self.DOWNLOAD_CHUNK_SIZE)
                finally:
                    rf.close()
            yield ntr.get_path()
        finally:
            ntr.finished()

    @contextmanager
    def make_stream(self):
        with self.make_path() as p:
            yield p.open("rb")

    DOWNLOAD_CHUNK_SIZE = 1024 * 512
