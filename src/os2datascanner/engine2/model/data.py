from .core import Source, Handle, FileResource, EMPTY_COOKIE

from io import BytesIO
from os import fsync
from base64 import b64decode, b64encode
from tempfile import NamedTemporaryFile
from contextlib import contextmanager

class DataSource(Source):
    def __init__(self, content, mime="application/octet-stream"):
        self._content = content
        self._mime = mime

    def handles(self, sm):
        yield DataHandle(self, "file")

    def __str__(self):
        return "DataSource(content=..., mime={0})".format(self._mime)

    def _open(self, sm):
        return EMPTY_COOKIE

    def _close(self, sm):
        pass

    def to_url(self):
        return "data:{0};base64,{1}".format(self._mime, b64encode(self._content).decode(encoding='ascii'))

    @staticmethod
    @Source.url_handler("data")
    def from_url(url):
        _, rest = url.split(':', maxsplit=1)
        mime, rest = rest.split(';', maxsplit=1)
        _, content = rest.split(',', maxsplit=1)
        return DataSource(b64decode(content), mime)

class DataHandle(Handle):
    def guess_type(self):
        return self.get_source()._mime

    def follow(self, sm):
        return DataResource(self, sm)

class DataResource(FileResource):
    def get_size(self):
        return len(self.get_handle().get_source()._content)

    def get_last_modified(self):
        return super().get_last_modified()

    @contextmanager
    def make_path(self):
        with NamedTemporaryFile() as fp, self.make_stream() as s:
            fp.write(s.read())
            fp.flush()
            fsync(fp.fileno())

            yield fp.name

    @contextmanager
    def make_stream(self):
        with BytesIO(self.get_handle().get_source()._content) as s:
            yield s
