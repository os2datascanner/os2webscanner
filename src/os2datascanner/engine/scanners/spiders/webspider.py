import logging
import magic
# Use our monkey-patched link extractor
from ..linkextractor import LxmlLinkExtractor

from scrapy.exceptions import IgnoreRequest
from scrapy.http import Request, HtmlResponse
from scrapy.spidermiddlewares.httperror import HttpError
from scrapy.utils.response import response_status_message

from .scanner_spider import ScannerSpider


class WebSpider(ScannerSpider):
    """A spider which uses a scanner to scan all data it comes across."""

    name = 'webscanner'
    magic = magic.Magic(mime=True)

    def __init__(self, scanner, runner, *a, **kw):
        """Initialize the ScannerSpider with a Scanner object.

        The configuration will be loaded from the Scanner.
        """
        super().__init__(scanner=scanner, runner=runner, *a, **kw)

    def setup_spider(self):
        logging.info("Initializing spider of type WebSpider")
        # If the scan is run from a web service, use the starting urls
        # from the scanner.
        if self.scanner.process_urls:
            self.start_urls = self.scanner.process_urls
        else:
            self.crawl = True
            # Otherwise, use the roots of the domains as starting URLs
            for url in self.allowed_domains:
                if (
                            not url.startswith('http://') and
                            not url.startswith('https://')
                ):
                    url = 'http://%s/' % url

                # Remove wildcards
                url = url.replace('*.', '')
                logging.info("Start url %s" % str(url))
                self.start_urls.append(url)

            self.link_extractor = LxmlLinkExtractor(
                deny_extensions=(),
                tags=('a', 'area', 'frame', 'iframe', 'script'),
                attrs=('href', 'src')
            )
            self.referrers = {}
            self.broken_url_objects = {}
            # Dict to cache referrer URL objects
            self.referrer_url_objects = {}
            self.external_urls = set()

    def start_requests(self):
        """Return requests for all starting URLs AND sitemap URLs."""
        # Add URLs found in sitemaps
        logging.info("Starting requests")
        sitemap_start_urls = self.runner.get_start_urls_from_sitemap()
        requests = []
        logging.info("Adding requests for {0} sitemap start URLs".format(
            len(sitemap_start_urls)))
        for url in sitemap_start_urls:
            try:
                logging.info("Adding request for sitemap URL {0}".format(url))
                requests.append(
                    Request(url["url"],
                            callback=self.parse,
                            errback=self.handle_error,
                            # Add the lastmod date from the sitemap
                            meta={"lastmod": url.get("lastmod", None)})
                )
            except Exception:
                logging.exception('adding request for url %r failed', url)

        for url in self.start_urls:
            try:
                requests.append(Request(url, callback=self.parse,
                                        errback=self.handle_error))
            except Exception:
                logging.exception('adding request for url %r failed', url)


        return requests

    def parse(self, response):
        """Process a response and follow all links."""
        if self.crawl:
            requests = self._extract_requests(response)
        else:
            requests = []

        self.scan(response)

        if self.scanner.do_link_check:
            source_url = response.request.url
            for request in requests:
                target_url = request.url
                self.referrers.setdefault(target_url, []).append(source_url)
                if (self.scanner.do_external_link_check and
                        self.is_offsite(request)):
                    # Save external URLs for later checking
                    self.external_urls.add(target_url)
                else:
                    # See if the link points to a broken URL
                    broken_url = self.broken_url_objects.get(target_url, None)
                    if broken_url is not None:
                        # Associate links to the broken URL
                        self.associate_url_referrers(broken_url)

        return requests

    def handle_error(self, failure):
        """Handle an error due to a non-success status code or other reason.

        If link checking is enabled, saves the broken URL and referrers.
        """
        try:
            logging.info("Handle error response status code: {}".format(failure.value.response))
            logging.info("Url that failed: {}".format(
                failure.value.response.request.url))
        except Exception:
            logging.error("Could not print handle error status code.")

        # If we should not do link check or failure is ignore request
        # and it is not a http error we know it is a last-modified check.
        if (not self.scanner.do_link_check or
                (isinstance(failure.value, IgnoreRequest) and not isinstance(
                    failure.value, HttpError))):
            logging.info("We do not do link check or failure is an instance of "
                         "IgnoreRequest: {}".format(failure.value))
            return

        if hasattr(failure.value, "response"):
            response = failure.value.response
            url = response.request.url
            status_code = response.status
            status_message = response_status_message(status_code)

            if "redirect_urls" in response.request.meta:
                # Set URL to the original URL, not the URL after redirection
                url = response.request.meta["redirect_urls"][0]

            referer_header = response.request.headers.get("referer", None)
        else:
            url = failure.request.url
            status_code = -1
            status_message = "%s" % failure.value
            referer_header = None

        broken_url = self.broken_url_save(status_code, status_message, url)

        self.broken_url_objects[url] = broken_url

        # Associate referer using referer heade
        if referer_header is not None:
            self.associate_url_referrer(referer_header, broken_url)

        self.associate_url_referrers(broken_url)

    def scan(self, response):
        """Scan a response, returning any matches."""
        super().scan(response)

    def _extract_requests(self, response):
        """Extract requests from the response."""
        r = []
        if isinstance(response, HtmlResponse):
            links = self.link_extractor.extract_links(response)
            r.extend(Request(x.url, callback=self.parse,
                             errback=self.handle_error) for x in links)
        return r

    def associate_url_referrers(self, url_object):
        """Associate referrers with the Url object."""
        for referrer in self.referrers.get(url_object.url, ()):
            self.associate_url_referrer(referrer, url_object)

    def associate_url_referrer(self, referrer, url_object):
        """Associate referrer with Url object."""
        referrer_url_object = self._get_or_create_referrer(referrer)
        url_object.referrers.add(referrer_url_object)

    def _get_or_create_referrer(self, referrer):
        """Create or get existing ReferrerUrl object."""
        from os2datascanner.sites.admin.adminapp.models.referrerurl_model import ReferrerUrl
        if referrer not in self.referrer_url_objects:
            self.referrer_url_objects[referrer] = ReferrerUrl(
                url=referrer, scan=self.scanner.scan_object)
            self.referrer_url_objects[referrer].save()
        return self.referrer_url_objects[referrer]
