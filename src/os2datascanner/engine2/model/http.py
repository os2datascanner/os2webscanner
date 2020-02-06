from io import BytesIO
from time import sleep
from lxml.html import document_fromstring
from urllib.parse import urljoin, urlsplit, urlunsplit
from dateutil.parser import parse as parse_date
from requests.sessions import Session
from requests.exceptions import ConnectionError
from contextlib import contextmanager

from ..rules.types import InputType
from ..conversions.utilities.results import MultipleResults
from .core import Source, Handle, FileResource, ResourceUnavailableError
from .utilities import NamedTemporaryResource


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

    def _generate_state(self, sm):
        with Session() as session:
            yield session

    def censor(self):
        # XXX: we should actually decompose the URL and remove authentication
        # details from netloc
        return self

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


class WebResource(FileResource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._status = None
        self._mr = None

    def _make_url(self):
        handle = self.handle
        base = handle.source.to_url()
        return base + str(handle.relative_path)

    def get_status(self):
        self.unpack_header()
        return self._status

    def unpack_header(self, check=False):
        if not self._status:
            response = self._get_cookie().head(self._make_url())
            self._status = response.status_code
            header = response.headers

            self._mr = MultipleResults(
                    {k.lower(): v for k, v in header.items()})
            try:
                self._mr[InputType.LastModified] = parse_date(
                        self._mr["last-modified"].value)
            except (KeyError, ValueError):
                pass
        if check:
            if self._status != 200:
                raise ResourceUnavailableError(self.handle, self._status)
        return self._mr

    def get_size(self):
        return self.unpack_header(check=True).get("content-length", 0).map(int)

    def get_last_modified(self):
        return self.unpack_header(check=True).setdefault(
                InputType.LastModified, super().get_last_modified())

    def compute_type(self):
        # At least for now, strip off any extra parameters the media type might
        # specify
        return self.unpack_header(check=True).get("content-type",
                "application/octet-stream").value.split(";", maxsplit=1)[0]

    @contextmanager
    def make_path(self):
        with NamedTemporaryResource(self.handle.name) as ntr:
            with ntr.open("wb") as res:
                with self.make_stream() as s:
                    res.write(s.read())
            yield ntr.get_path()

    @contextmanager
    def make_stream(self):
        response = self._get_cookie().get(self._make_url())
        if response.status_code != 200:
            raise ResourceUnavailableError(self.handle, response.status_code)
        else:
            with BytesIO(response.content) as s:
                yield s


@Handle.stock_json_handler("web")
class WebHandle(Handle):
    type_label = "web"
    resource_type = WebResource

    eq_properties = Handle.BASE_PROPERTIES

    def __init__(self, source, path):
        super().__init__(source, path)
        self._referrer_urls = set()

    def set_referrer_urls(self, referrer_urls):
        self._referrer_urls = referrer_urls

    def get_referrer_urls(self):
        return self._referrer_urls

    @property
    def presentation(self):
        return self.presentation_url

    @property
    def presentation_url(self):
        p = self.source.to_url()
        if p[-1] != "/":
            p += "/"
        return p + self.relative_path

    def censor(self):
        return WebHandle(self.source.censor(), self.relative_path)
