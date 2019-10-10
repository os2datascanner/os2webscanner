from .core import Source, Handle, FileResource, EMPTY_COOKIE

from io import BytesIO
from os import fsync
from base64 import b64decode, b64encode
from tempfile import NamedTemporaryFile
from contextlib import contextmanager

class DataSource(Source):
    type_label = "data"

    def __init__(self, content, mime="application/octet-stream"):
        self._content = content
        self._mime = mime

    def handles(self, sm):
        yield DataHandle(self, "file")

    def __str__(self):
        return "DataSource(content=..., mime={0})".format(self._mime)

    def _generate_state(self, sm):
        yield EMPTY_COOKIE

    def to_url(self):
        return "data:{0};base64,{1}".format(self._mime, b64encode(self._content).decode(encoding='ascii'))

    @staticmethod
    @Source.url_handler("data")
    def from_url(url):
        _, rest = url.split(':', maxsplit=1)
        mime, rest = rest.split(';', maxsplit=1)
        _, content = rest.split(',', maxsplit=1)
        return DataSource(b64decode(content), mime)

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "content": b64encode(self._content).decode(encoding="ascii"),
            "mime": self._mime
        })

    @staticmethod
    @Source.json_handler(type_label)
    def from_json_object(obj):
        return DataSource(b64decode(obj["content"]), obj["mime"])

class DataHandle(Handle):
    type_label = "data"

    def guess_type(self):
        return self.get_source()._mime

    def follow(self, sm):
        return DataResource(self, sm)
Handle.stock_json_handler(DataHandle.type_label, DataHandle)

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
