from urllib3 import HTTPConnectionPool
from utilities import NamedTemporaryResource
from dateutil.parser import parse

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

    def __enter__(self):
        assert not self._ntr
        try:
            response = self._open_source().request(
                    "GET", str(self._handle.get_relative_path()))
            self._ntr = _NamedTemporaryResource(self._handle.get_name())
            with self._ntr.open("wb") as res:
                res.write(response.data)
            return self._ntr.get_path()
        except:
            raise

    def __exit__(self, exc_type, exc_value, traceback):
        assert self._ntr
        self._ntr.finished()
        self._ntr = None
