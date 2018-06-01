# The contents of this file are subject to the Mozilla Public License
# Version 2.0 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
#    http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# OS2Webscanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (http://www.os2web.dk/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( http://www.os2web.dk/ )
"""Contains a scanner spider."""
import mimetypes

from os2webscanner.utils import capitalize_first
import regex
import logging

from scrapy.spidermiddlewares.httperror import HttpError
from scrapy.exceptions import IgnoreRequest
from scrapy.http import Request, HtmlResponse
import re
import chardet
import magic
import logging

# Use our monkey-patched link extractor
from ..linkextractor import LxmlLinkExtractor

from .base_spider import BaseScannerSpider

from ..processors.processor import Processor

from os2webscanner.models import Url, ReferrerUrl
from scrapy.utils.response import response_status_message


class ScannerSpider(BaseScannerSpider):

    """A spider which uses a scanner to scan all data it comes across."""

    name = 'scanner'
    magic = magic.Magic(mime=True)

    def __init__(self, scanner, runner, *a, **kw):
        """Initialize the ScannerSpider with a Scanner object.

        The configuration will be loaded from the Scanner.
        """
        super(ScannerSpider, self).__init__(scanner=scanner, *a, **kw)

        self.runner = runner

        self.start_urls = []

        if self.scanner.scan_object.scanner.process_urls:
            # If the scan is run from a web service, use the starting urls
            # from the scanner.
            self.start_urls = self.scanner.scan_object.scanner.process_urls
            self.crawl = False
        else:
            self.crawl = True
            # Otherwise, use the roots of the domains as starting URLs
            logging.info("Initializing spider")
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

        # Read from Scanner settings
        scan_object = self.scanner.scan_object
        self.do_last_modified_check = getattr(
            scan_object, "do_last_modified_check"
        )
        self.do_last_modified_check_head_request = getattr(
            scan_object, "do_last_modified_check_head_request"
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
        for url in sitemap_start_urls:
            try:
                requests.append(
                    Request(url["url"],
                            callback=self.parse,
                            errback=self.handle_error,
                            # Add the lastmod date from the sitemap
                            meta={"lastmod": url.get("lastmod", None)})
                )
            except Exception as e:
                logging.error("URL failed: {0} ({1})".format(url, str(e)))

        logging.info("Number of urls to scan %s" % str(len(self.start_urls)))
        #yield Request(self.start_urls[0], callback=self.parse,
         #       errback=self.handle_error)
        requests.extend([Request(url, callback=self.parse,
                                 errback=self.handle_error)
                         for url in self.start_urls])
        logging.info("Number of requests %s" % str(len(requests)))
        return requests

    def parse(self, response):
        """Process a response and follow all links."""
        if self.crawl:
            requests = self._extract_requests(response)
        else:
            requests = []
        self.scan(response)

        # Store referrer when doing link checks
        if self.scanner.scan_object.do_link_check:
            source_url = response.request.url
            for request in requests:
                target_url = request.url
                self.referrers.setdefault(target_url, []).append(source_url)
                if (self.scanner.scan_object.do_external_link_check and
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

    def _extract_requests(self, response):
        """Extract requests from the response."""
        logging.info("Extract request.")
        r = []
        if isinstance(response, HtmlResponse):
            links = self.link_extractor.extract_links(response)
            logging.debug("Extracted links: %s" % links)
            r.extend(Request(x.url, callback=self.parse,
                             errback=self.handle_error) for x in links)
        return r

    def handle_error(self, failure):
        """Handle an error due to a non-success status code or other reason.

        If link checking is enabled, saves the broken URL and referrers.
        """
        if (not self.scanner.scan_object.do_link_check or
                (isinstance(failure.value, IgnoreRequest) and not isinstance(
                    failure.value, HttpError))):
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

        logging.info("Handle Error: %s %s" % (status_message, url))

        status_message = regex.sub("\[.+\] ", "", status_message)
        status_message = capitalize_first(status_message)

        # Add broken URL
        broken_url = Url(url=url, scan=self.scanner.scan_object,
                         status_code=status_code,
                         status_message=status_message)
        broken_url.save()
        self.broken_url_objects[url] = broken_url

        # Associate referer using referer header
        if referer_header is not None:
            self.associate_url_referrer(referer_header, broken_url)

        self.associate_url_referrers(broken_url)

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
        if referrer not in self.referrer_url_objects:
            self.referrer_url_objects[referrer] = ReferrerUrl(
                url=referrer, scan=self.scanner.scan_object)
            self.referrer_url_objects[referrer].save()
        return self.referrer_url_objects[referrer]

    def scan(self, response):
        """Scan a response, returning any matches."""
        content_type = response.headers.get('content-type')
        if content_type:
            mime_type = parse_content_type(content_type)
        else:
            logging.debug("Guessing mime-type based on file extension")
            mime_type, encoding = mimetypes.guess_type(response.url)
            if not mime_type:
                logging.debug("Guessing mime-type based on file contents")
                mime_type = self.magic.from_buffer(response.body)

        data, mime_type = self.check_encoding(mime_type, response)
        # Save the URL item to the database
        if (
            Processor.mimetype_to_processor_type(mime_type) == 'ocr' and not
            self.scanner.scan_object.do_ocr
        ):
            # Ignore this URL
            return
        url_object = Url(url=response.request.url, mime_type=mime_type,
                         scan=self.scanner.scan_object)
        url_object.save()
        self.scanner.scan(data, url_object)

    def check_encoding(self, mime_type, response):
        if hasattr(response, "encoding"):
            try:
                data = response.body.decode(response.encoding)
            except UnicodeDecodeError:
                try:
                    # Encoding specified in Content-Type header was wrong, try
                    # to detect the encoding and decode again
                    encoding = chardet.detect(response.body).get('encoding')
                    if encoding is not None:
                        data = response.body.decode(encoding)
                        logging.warning(
                            (
                                "Error decoding response as %s. " +
                                "Detected the encoding as %s.") %
                            (response.encoding, encoding)
                        )
                    else:
                        mime_type = self.magic.from_buffer(response.body)
                        data = response.body
                        logging.warning(("Error decoding response as %s. " +
                                 "Detected the mime " +
                                 "type as %s.") % (response.encoding,
                                                   mime_type))
                except UnicodeDecodeError:
                    # Could not decode with the detected encoding, so assume
                    # the file is binary and try to guess the mimetype from
                    # the file
                    mime_type = self.magic.from_buffer(response.body)
                    data = response.body
                    logging.error(
                        ("Error decoding response as %s. Detected the "
                         "mime type as %s.") % (response.encoding,
                                                mime_type)
                    )

        else:
            data = response.body

        return data, mime_type


def parse_content_type(content_type):
    """Return the mime-type from the given "Content-Type" header value."""
    # For some reason content_type can be a binary string.
    if type(content_type) is not str:
        content_type = content_type.decode('utf8')

    logging.debug("Content-Type: " + content_type)
    m = re.search('([^/]+/[^;\s]+)', content_type)
    return m.group(1)
