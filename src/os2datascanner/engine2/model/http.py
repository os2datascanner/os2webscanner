from .core import Source, Handle, FileResource
from .utilities import NamedTemporaryResource

from io import BytesIO
from requests.sessions import Session
from contextlib import contextmanager

class WebSource(Source):
    def __init__(self, url):
        assert url.startswith("http:") or url.startswith("https:")
        self._url = url

    def __str__(self):
        return "WebSource({0})".format(self._url)

    def _open(self, sm):
        return Session()

    def _close(self, session):
        session.close()

    def handles(self, sm):
        pass

    def to_url(self):
        return self._url

    @staticmethod
    @Source.url_handler("http", "https")
    def from_url(url):
        return WebSource(url)

SecureWebSource = WebSource

class WebHandle(Handle):
    def follow(self, sm):
        return WebResource(self, sm)

class WebResource(FileResource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._header = None

    def _make_url(self):
        handle = self.get_handle()
        base = handle.get_source().to_url()
        return base + str(handle.get_relative_path())

    def get_header(self):
        if not self._header:
            response = self._open_source().head(self._make_url())
            self._header = dict(response.headers)
        return self._header

    def get_last_modified(self):
        return dateutil.parse(self.get_header()["Last-Modified"])

    # override
    def compute_type(self):
        return self.get_header()["Content-Type"] or "application/octet-stream"

    @contextmanager
    def make_path(self):
        ntr = NamedTemporaryResource(self._handle.get_name())
        try:
            with ntr.open("wb") as res:
                with self.make_stream() as s:
                    res.write(s.read())
            yield ntr.get_path()
        finally:
            ntr.finished()

    @contextmanager
    def make_stream(self):
        response = self._open_source().get(self._make_url())
        with BytesIO(response.content) as s:
            yield s
