from model.core import Source, Handle
from model.file import FilesystemResource

from os import rmdir
from pathlib import Path
from tempfile import mkdtemp
from subprocess import run

class SMBSource(Source):
    def __init__(self, unc, user='', password='', domain=''):
        self._unc = unc
        self._user = user
        self._password = password
        self._domain = domain

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
        args = ["mount", "-t", "cifs", self._unc, mntdir, '-o']
        args.append(self._make_optarg(display=False))

        try:
            print(args)
            assert run(args).returncode == 0
            return Path(mntdir)
        except:
            rmdir(mntdir)
            raise

    def _close(self, mntdir):
        mntdir = str(mntdir)
        args = ["umount", mntdir]
        try:
            assert run(args).returncode == 0
        except:
            raise
        finally:
            rmdir(mntdir)

    def files(self, sm):
        mntdir = sm.open(self)
        for d in mntdir.glob("**"):
            for f in d.iterdir():
                if f.is_file():
                    yield SMBHandle(self, f.relative_to(mntdir))

class SMBHandle(Handle):
    def __init__(self, source, relpath):
        super(SMBHandle, self).__init__(source, relpath)

    def follow(self, sm):
        return FilesystemResource(self, sm)
