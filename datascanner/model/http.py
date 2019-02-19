from model.core import Source, Handle, Resource
from model.utilities import NamedTemporaryResource

from urllib.parse import urlsplit, urlunsplit
from urllib3 import HTTPConnectionPool, HTTPSConnectionPool
from dateutil.parser import parse
from contextlib import contextmanager

class WebSource(Source):
    def __init__(self, host, port=80):
        self._host = host
        self._port = port

    def __str__(self):
        return "WebSource({0}:{1})".format(self._host, self._port)

    def _open(self, sm):
        return HTTPConnectionPool(self._host, self._port)

    def _close(self, pool):
        pool.close()

    def to_url(self):
        netloc = \
            self._host + ((':' + self._port) if not self._port == 80 else '')
        return urlunsplit(('http', netloc, '', None, None))

    @staticmethod
    def from_url(url):
        scheme, netloc, path, _, _ = urlsplit(url)
        assert not path
        host = netloc.split(':', maxsplit=1)
        return WebSource(host[0], 80 if len(host) == 1 else int(host[1]))

Source._register_url_handler("http", WebSource.from_url)

class SecureWebSource(WebSource):
    def __init__(self, host, port=443):
        super(SecureWebSource, self).__init__(host, port)

    def __str__(self):
        return "SecureWebSource({0}:{1})".format(self._host, self._port)

    def _open(self, sm):
        return HTTPSConnectionPool(self._host, self._port)

    def to_url(self):
        netloc = \
            self._host + ((':' + self._port) if not self._port == 443 else '')
        return urlunsplit(('https', netloc, '', None, None))

    @staticmethod
    def from_url(url):
        scheme, netloc, path, _, _ = urlsplit(url)
        assert not path
        host = netloc.split(':', maxsplit=1)
        return SecureWebSource(host[0], 443 if len(host) == 1 else int(host[1]))

Source._register_url_handler("https", SecureWebSource.from_url)

class WebHandle(Handle):
    def __init__(self, source, path):
        super(WebHandle, self).__init__(source, path)

    def follow(self, sm):
        return WebResource(self, sm)

class WebResource(Resource):
    def __init__(self, handle, sm):
        super(WebResource, self).__init__(handle, sm)
        self._header = None
        self._ntr = None

    def get_header(self):
        if not self._header:
            response = self._open_source().request(
                    "HEAD", str(self._handle.get_relative_path()))
            self._header = dict(response.headers)
        return self._header

    def get_last_modified(self):
        return dateutil.parse(self.get_header()["Last-Modified"])

    # override
    def compute_type(self):
        return self.get_header()["Content-Type"] \
                or "application/octet-stream"

    @contextmanager
    def make_path(self):
        ntr = NamedTemporaryResource(self._handle.get_name())
        try:
            response = self._open_source().request(
                    "GET", str(self._handle.get_relative_path()))
            with ntr.open("wb") as res:
                res.write(response.data)
            yield ntr.get_path()
        finally:
            ntr.finished()

