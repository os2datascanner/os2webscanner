from .core import Source, Handle
from .file import FilesystemResource

from os import rmdir
from regex import compile
from urllib.parse import quote, unquote, urlsplit, urlunsplit
from pathlib import Path
from tempfile import mkdtemp
from subprocess import run


class SMBSource(Source):
    type_label = "smb"
    eq_properties = ("_unc", "_user", "_password", "_domain",)

    def __init__(self, unc, user=None, password=None, domain=None,
            driveletter=None):
        self._unc = unc
        self._user = user
        self._password = password
        self._domain = domain
        self._driveletter = driveletter

    @property
    def unc(self):
        return self._unc

    @property
    def driveletter(self):
        return self._driveletter

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

    def _generate_state(self, sm):
        mntdir = mkdtemp()
        try:
            args = ["mount", "-t", "cifs", self._unc, mntdir, '-o']
            args.append(self._make_optarg(display=False))
            print(args)
            assert run(args).returncode == 0

            yield mntdir
        finally:
            try:
                assert run(["umount", mntdir]).returncode == 0
            finally:
                rmdir(mntdir)

    def censor(self):
        return SMBSource(self.unc, None, None, None, self.driveletter)

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

    netloc_regex = compile(r"^(((?P<domain>\w+);)?(?P<username>\w+)(:(?P<password>\w+))?@)?(?P<unc>[\w.-]+)$")
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
            "domain": self._domain,
            "driveletter": self._driveletter
        })

    @staticmethod
    @Source.json_handler(type_label)
    def from_json_object(obj):
        return SMBSource(
                obj["unc"], obj["user"], obj["password"], obj["domain"],
                obj["driveletter"])


@Handle.stock_json_handler("smb")
class SMBHandle(Handle):
    type_label = "smb"
    resource_type = FilesystemResource

    @property
    def presentation(self):
        p = self.source.driveletter
        if p:
            p += ":"
        else:
            p = self.source.unc
        if p[-1] != "/":
            p += "/"
        return (p + self.relative_path).replace("/", "\\")

    def censor(self):
        return SMBHandle(self.source.censor(), self.relative_path)


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
