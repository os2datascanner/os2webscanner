from .core import Source, Handle, Resource, EMPTY_COOKIE

from io import BytesIO
from os import remove
from base64 import b64decode, b64encode
from hashlib import md5
from pathlib import Path
from tempfile import NamedTemporaryFile
from contextlib import contextmanager

class DataSource(Source):
    def __init__(self, content, mime="application/octet-stream"):
        self._content = content
        self._mime = mime

    def handles(self, sm):
        yield DataHandle(self, Path())

    def __str__(self):
        return "DataSource(content=..., mime={0})".format(self._mime)

    def _open(self, sm):
        return EMPTY_COOKIE

    def _close(self, sm):
        pass

    def to_url(self):
        return "data:{0};base64,{1}".format(self._mime, b64encode(self._content).decode(encoding='ascii'))

    @staticmethod
    def from_url(url):
        _, rest = url.split(':', maxsplit=1)
        mime, rest = rest.split(';', maxsplit=1)
        _, content = rest.split(',', maxsplit=1)
        return DataSource(b64decode(content), mime)

Source._register_url_handler('data', DataSource.from_url)

class DataHandle(Handle):
    def __init__(self, source, relpath):
        super(DataHandle, self).__init__(source, relpath)

    def guess_type(self):
        return self.get_source()._mime

    def follow(self, sm):
        return DataResource(self, sm)

class DataResource(Resource):
    def __init__(self, handle, sm):
        super(DataResource, self).__init__(handle, sm)
        self._hash = None

    def get_hash(self):
        if not self._hash:
            with self.make_stream() as s:
                self._hash = md5(s.read())
        return self._hash

    def get_last_modified(self):
        return None

    @contextmanager
    def make_path(self):
        ntf = NamedTemporaryFile(delete=False)
        try:
            with ntf as res:
                with self.make_stream() as s:
                    res.write(s.read())
            yield ntf.name
        finally:
            remove(ntf.name)

    @contextmanager
    def make_stream(self):
        with BytesIO(self.get_handle().get_source()._content) as s:
            yield s
