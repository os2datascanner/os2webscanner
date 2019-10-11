from .core import Source, Handle, FileResource, ResourceUnavailableError
from .utilities import NamedTemporaryResource

from io import BytesIO
from time import sleep
from lxml.html import document_fromstring
from urllib.parse import urljoin, urlsplit, urlunsplit
from dateutil.parser import parse as parse_date
from requests.sessions import Session
from requests.exceptions import ConnectionError
from contextlib import contextmanager

MAX_REQUESTS_PER_SECOND = 10
SLEEP_TIME = 1 / MAX_REQUESTS_PER_SECOND

def simplify_mime_type(mime):
    r = mime.split(';', maxsplit=1)
    return r[0]

class WebSource(Source):
    type_label = "web"

    def __init__(self, url):
        assert url.startswith("http:") or url.startswith("https:")
        self._url = url

    def __str__(self):
        return "WebSource({0})".format(self._url)

    def _generate_state(self, sm):
        with Session() as session:
            yield session

    def handles(self, sm):
        try:
            session = sm.open(self)
            to_visit = [self._url]
            visited = set()
            referrer_map = {}

            scheme, netloc, path, query, fragment = urlsplit(self._url)
            while to_visit:
                here, to_visit = to_visit[0], to_visit[1:]

                response = session.head(here)
                if response.status_code == 200:
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
                                referrer_map.setdefault(new_url, set()).add(here)
                                if new_url not in visited:
                                    visited.add(new_url)
                                    to_visit.append(new_url)

                wh = WebHandle(self, here[len(self._url):])
                wh.set_referrer_urls(referrer_map.get(here, set()))
                yield wh
                sleep(SLEEP_TIME)
        except ConnectionError as e:
            raise ResourceUnavailableError(self, *e.args)

    def to_url(self):
        return self._url

    @staticmethod
    @Source.url_handler("http", "https")
    def from_url(url):
        return WebSource(url)

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "url": self._url
        })

    @staticmethod
    @Source.json_handler(type_label)
    def from_json_object(obj):
        return WebSource(url=obj["url"])

SecureWebSource = WebSource

class WebHandle(Handle):
    type_label = "web"

    eq_properties = Handle.BASE_PROPERTIES

    def __init__(self, source, path):
        super().__init__(source, path)
        self._referrer_urls = set()

    def set_referrer_urls(self, referrer_urls):
        self._referrer_urls = referrer_urls

    def get_referrer_urls(self):
        return self._referrer_urls

    def follow(self, sm):
        return WebResource(self, sm)
Handle.stock_json_handler(WebHandle.type_label, WebHandle)

class WebResource(FileResource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._status = None
        self._header = None

    def _make_url(self):
        handle = self.get_handle()
        base = handle.get_source().to_url()
        return base + str(handle.get_relative_path())

    def _require_header_and_status(self):
        if not self._header:
            response = self._get_cookie().head(self._make_url())
            self._status = response.status_code
            self._header = response.headers.copy()

    def get_status(self):
        self._require_header_and_status()
        return self._status

    def get_header(self):
        self._require_header_and_status()
        if self._status != 200:
            raise ResourceUnavailableError(self.get_handle(), self._status)
        return self._header

    def get_size(self):
        return int(self.get_header()["Content-Length"])

    def get_last_modified(self):
        try:
            return parse_date(self.get_header()["Last-Modified"])
        except (KeyError, ValueError):
            return super().get_last_modified()

    # override
    def compute_type(self):
        # At least for now, strip off any extra parameters the media type might
        # specify
        return self.get_header().get("Content-Type",
                "application/octet-stream").split(";", maxsplit=1)[0]

    @contextmanager
    def make_path(self):
        ntr = NamedTemporaryResource(self.get_handle().get_name())
        try:
            with ntr.open("wb") as res:
                with self.make_stream() as s:
                    res.write(s.read())
            yield ntr.get_path()
        finally:
            ntr.finished()

    @contextmanager
    def make_stream(self):
        response = self._get_cookie().get(self._make_url())
        if response.status_code != 200:
            raise ResourceUnavailableError(
                    self.get_handle(), response.status_code)
        else:
            with BytesIO(response.content) as s:
                yield s
