from .smb import make_smb_url, SMBSource
from .core import Source, Handle, FileResource, ResourceUnavailableError
from .utilities import NamedTemporaryResource

import io
from os import stat_result, O_RDONLY
import smbc
from urllib.parse import quote, unquote, urlsplit
from datetime import datetime
from contextlib import contextmanager


class SMBCSource(Source):
    type_label = "smbc"
    eq_properties = ("_unc", "_user", "_password", "_domain",)

    def __init__(self, unc, user=None, password=None, domain=None,
            driveletter=None):
        self._unc = unc
        self._user = user
        self._password = password
        self._domain = domain
        self._driveletter = driveletter

    def get_unc(self):
        return self._unc

    def get_driveletter(self):
        return self._driveletter

    def __str__(self):
        return "SMBCSource({0}, {1}, ****, {2})".format(
                self._unc, self._user, self._domain)

    def _generate_state(self, sm):
        c = smbc.Context()
        try:
            yield (self._to_url(), c)
        finally:
            # Brutal, but apparently necessary to shut the connection down...
            del c

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

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "unc": self._unc,
            "user": self._user,
            "password": self._password,
            "domain": self._domain,
            "driveletter": self._driveletter
        })

    @staticmethod
    @Source.json_handler(type_label)
    def from_json_object(obj):
        return SMBCSource(
                obj["unc"], obj["user"], obj["password"], obj["domain"],
                obj["driveletter"])


@Handle.stock_json_handler("smbc")
class SMBCHandle(Handle):
    type_label = "smbc"

    @property
    def presentation(self):
        p = self.source.get_driveletter()
        if p:
            p += ":"
        else:
            p = self.source.get_unc()
        if p[-1] != "/":
            p += "/"
        return (p + self.relative_path).replace("/", "\\")

    def follow(self, sm):
        return SMBCResource(self, sm)


class _SMBCFile(io.RawIOBase):
    def __init__(self, obj):
        self._file = obj

    def readinto(self, b):
        data = self._file.read(len(b))
        count = len(data)
        b[0:count] = data
        return count

    def write(self, bytes):
        raise TypeError("_SMBCFile is read-only")

    def seek(self, pos, whence):
        r = self._file.lseek(pos, whence)
        if r != -1:
            return r
        else:
            raise IOError("lseek failed")

    def tell(self):
        r = self._file.lseek(0, io.SEEK_CUR)
        if r != -1:
            return r
        else:
            raise IOError("lseek failed")

    def truncate(self, n=None):
        raise TypeError("_SMBCFile is read-only")

    def close(self):
        r = self._file.close()
        if r and r < 0:
            raise IOError("Failed to close {0}".format(self), r)

    def readable(self):
        return True

    def writable(self):
        return False

    def seekable(self):
        return True


class SMBCResource(FileResource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._stat = None

    def _make_url(self):
        url, _ = self._get_cookie()
        return url + "/" + quote(self.handle.relative_path)

    def open_file(self):
        try:
            _, context = self._get_cookie()
            return context.open(self._make_url(), O_RDONLY)
        except (smbc.NoEntryError, smbc.PermissionError) as ex:
            raise ResourceUnavailableError(self.handle, ex)

    def get_xattr(self, attr):
        """Retrieves a SMB extended attribute for this file. (See the
        documentation for smbc.Context.getxattr for *most* of the supported
        attribute names.)"""
        try:
            _, context = self._get_cookie()
            return context.getxattr(self._make_url(), attr)
            # Don't attempt to catch the ValueError if attr isn't valid
        except (smbc.NoEntryError, smbc.PermissionError) as ex:
            raise ResourceUnavailableError(self.handle, ex)

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

    def get_owner_sid(self):
        """Returns the Windows security identifier of the owner of this file,
        which libsmbclient exposes as an extended attribute."""
        return self.get_xattr("system.nt_sec_desc.owner")

    @contextmanager
    def make_path(self):
        ntr = NamedTemporaryResource(self.handle.name)
        try:
            with ntr.open("wb") as f:
                with self.make_stream() as rf:
                    buf = rf.read(self.DOWNLOAD_CHUNK_SIZE)
                    while buf:
                        f.write(buf)
                        buf = rf.read(self.DOWNLOAD_CHUNK_SIZE)
            yield ntr.get_path()
        finally:
            ntr.finished()

    @contextmanager
    def make_stream(self):
        with _SMBCFile(self.open_file()) as fp:
            yield fp

    DOWNLOAD_CHUNK_SIZE = 1024 * 512
