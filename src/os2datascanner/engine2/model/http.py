from .core import Source, Handle, FileResource
from .utilities import NamedTemporaryResource

from io import BytesIO
from time import sleep
from lxml.html import document_fromstring
from urllib.parse import urljoin, urlsplit, urlunsplit
from requests.sessions import Session
from contextlib import contextmanager

MAX_REQUESTS_PER_SECOND = 10
SLEEP_TIME = 1 / MAX_REQUESTS_PER_SECOND

def simplify_mime_type(mime):
    r = mime.split(';', maxsplit=1)
    return r[0]

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
        session = sm.open(self)
        to_visit = [self._url]
        visited = set()

        scheme, netloc, path, query, fragment = urlsplit(self._url)
        while to_visit:
            here, to_visit = to_visit[0], to_visit[1:]

            response = session.head(here)
            if response.status_code != 200:
                print(here, response)
                continue

            ct = response.headers['Content-Type']
            if simplify_mime_type(ct) == 'text/html':
                response = session.get(here)
                doc = document_fromstring(response.content)
                doc.make_links_absolute(here, resolve_base_href=True)
                for el, _, li, _ in doc.iterlinks():
                    if el.tag != 'a':
                        continue
                    new_url = urljoin(here, li)
                    new_scheme, new_netloc, new_path, new_query, _ = urlsplit(new_url)
                    if new_scheme == scheme and new_netloc == netloc:
                        new_url = urlunsplit((new_scheme, new_netloc, new_path, new_query, None))
                        if new_url not in visited:
                            visited.add(new_url)
                            to_visit.append(new_url)

            yield WebHandle(self, here[len(self._url):])
            sleep(SLEEP_TIME)

        print(visited)

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
