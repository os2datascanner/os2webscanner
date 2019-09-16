from .core import Source, Handle, ShareableCookie
from .file import FilesystemResource

from os import rmdir
from regex import compile
from urllib.parse import quote, unquote, urlsplit, urlunsplit
from pathlib import Path
from tempfile import mkdtemp
from subprocess import run

class SMBSource(Source):
    type_label = "smb"

    def __init__(self, unc, user=None, password=None, domain=None):
        self._unc = unc
        self._user = user
        self._password = password
        self._domain = domain

    def get_unc(self):
        return self._unc

    def _make_optarg(self, display=True):
        optarg = ["ro"]
        if self._user:
            optarg.append('user=' + self._user)
        if self._password:
            optarg.append(
                    'password=' + (self._password if not display else "****"))
        else:
            optarg.append('guest')
        if self._domain:
            optarg.append('domain=' + self._domain)
        return ",".join(optarg)

    def __str__(self):
        return "SMBSource({0}, {1})".format(self._unc, self._make_optarg())

    def _open(self, sm):
        mntdir = mkdtemp()
        try:
            args = ["mount", "-t", "cifs", self._unc, mntdir, '-o']
            args.append(self._make_optarg(display=False))
            print(args)
            assert run(args).returncode == 0
            return ShareableCookie(mntdir)
        except:
            rmdir(mntdir)
            raise

    def _close(self, mntdir):
        args = ["umount", mntdir]
        try:
            assert run(args).returncode == 0
        except:
            raise
        finally:
            rmdir(mntdir)

    def handles(self, sm):
        pathlib_mntdir = Path(sm.open(self))
        for d in pathlib_mntdir.glob("**"):
            for f in d.iterdir():
                if f.is_file():
                    yield SMBHandle(self, str(f.relative_to(pathlib_mntdir)))

    def to_url(self):
        return make_smb_url(
                "smb", self._unc, self._user, self._domain, self._password)

    netloc_regex = compile(r"^(((?P<domain>\w+);)?(?P<username>\w+)(:(?P<password>\w+))?@)?(?P<unc>[\w.]+)$")
    @staticmethod
    @Source.url_handler("smb")
    def from_url(url):
        scheme, netloc, path, _, _ = urlsplit(url.replace("\\", "/"))
        match = SMBSource.netloc_regex.match(netloc)
        if match:
            return SMBSource("//" + match.group("unc") + unquote(path),
                match.group("username"), match.group("password"),
                match.group("domain"))
        else:
            return None

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "unc": self._unc,
            "user": self._user,
            "password": self._password,
            "domain": self._domain
        })

    @staticmethod
    @Source.json_handler(type_label)
    def from_json_object(obj):
        return SMBSource(
                obj["unc"], obj["user"], obj["password"], obj["domain"])

class SMBHandle(Handle):
    type_label = "smb"

    def follow(self, sm):
        return FilesystemResource(self, sm)
Handle.stock_json_handler(SMBHandle.type_label, SMBHandle)

# Third form from https://www.iana.org/assignments/uri-schemes/prov/smb
def make_smb_url(schema, unc, user, domain, password):
    server, path = unc.replace("\\", "/").lstrip('/').split('/', maxsplit=1)
    netloc = ""
    if user:
        if domain:
            netloc += domain + ";"
        netloc += user
        if password:
            netloc += ":" + password
        netloc += "@"
    netloc += server
    return urlunsplit((schema, netloc, quote(path), None, None))
