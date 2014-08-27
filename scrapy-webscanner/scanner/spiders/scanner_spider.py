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

from scrapy import log
from scrapy.contrib.spiders.sitemap import SitemapSpider
from scrapy.http import Request, HtmlResponse
from scrapy.contrib.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.utils.httpobj import urlparse_cached
from scrapy.utils.request import request_fingerprint

import re
import chardet
import mimetypes
import magic
from scrapy.utils.url import canonicalize_url

from ..processors.processor import Processor

from os2webscanner.models import Url, ReferrerUrl, UrlLastModified
from scrapy.utils.response import response_status_message


class ScannerSpider(SitemapSpider):

    """A spider which uses a scanner to scan all data it comes across."""

    name = 'scanner'
    magic = magic.Magic(mime=True)

    def __init__(self, scanner, *a, **kw):
        """Initialize the ScannerSpider with a Scanner object.

        The configuration will be loaded from the Scanner.
        """
        # Create scanner
        self.scanner = scanner

        self.exclusion_rules = self.scanner.get_exclusion_rules()
        self.allowed_domains = self.scanner.get_domains()
        self.sitemap_urls = self.scanner.get_sitemap_urls()

        # Follow alternate links in sitemaps (links to the same content in
        # different languages)
        self.sitemap_alternate_links = True

        SitemapSpider.__init__(self, *a, **kw)

        self.start_urls = []
        # TODO: Starting URLs and domains should be specified separately?
        for url in self.allowed_domains:
            if (not url.startswith('http://')
                and not url.startswith('https://')):
                url = 'http://%s/' % url
            self.start_urls.append(url)

        # TODO: Add more tags to extract links from?
        self.link_extractor = LxmlLinkExtractor(
            deny_extensions=(),
            tags=('a', 'area', 'frame', 'iframe', 'script'),
            attrs=('href', 'src')
        )

        # TODO: Read from Scanner settings
        self.do_last_modified_check = True
        self.do_last_modified_check_head_request = True

        self.referrers = {}
        self.external_urls = set()

    def start_requests(self):
        """Return requests for all starting URLs AND sitemap URLs."""
        requests = [Request(url, callback=self.parse, errback=self.handle_error)
                    for url in self.start_urls]
        sitemap_requests = list(SitemapSpider.start_requests(self))
        # Skip the last-modified check when requesting sitemaps
        for request in sitemap_requests:
            request.meta["skip_modified_check"] = True
        requests.extend(sitemap_requests)
        return requests

    def parse(self, response):
        """Process a response and follow all links."""
        r = []
        r.extend(self._extract_requests(response))
        self.scan(response)

        # Store referrer when doing link checks
        if self.scanner.do_link_check:
            source_url = response.request.url
            for request in r:
                target_url = request.url
                self.referrers.setdefault(target_url, []).append(source_url)

                # Save external URLs for later checking
                if self.scanner.do_external_link_check and self.is_offsite(request):
                    self.external_urls.add(target_url)

        return r

    def _extract_requests(self, response):
        """Extract requests from the response."""
        r = []
        if isinstance(response, HtmlResponse):
            links = self.link_extractor.extract_links(response)
            log.msg("Extracted links: %s" % links, level=log.DEBUG)
            r.extend(Request(x.url, callback=self.parse,
                             errback=self.handle_error) for x in links)
        return r

    def is_offsite(self, request):
        regex = self.get_host_regex()
        host = urlparse_cached(request).hostname or ''
        return not bool(regex.search(host))

    def is_excluded(self, request):
        # Build a string to match against, containing the path, and if
        # present, the query and fragment as well.
        url = urlparse_cached(request)
        match_against = url.path
        if url.query != '':
            match_against += "?" + url.query
        if url.fragment != '':
            match_against += "#" + url.fragment

        for rule in self.exclusion_rules:
            if isinstance(rule, basestring):
                # Do case-insensitive substring search
                if match_against.lower().find(rule.lower()) != -1:
                    return True
            else:
                # Do regex search against the URL
                if rule.search(match_against) is not None:
                    return True
        return False

    def get_host_regex(self):
        if not self.allowed_domains:
            return re.compile('')  # allow all by default
        regex = r'^(www\.)?(%s)$' % '|'.join(re.escape(d) for d in
                                             self.allowed_domains
                                             if d is not None)
        return re.compile(regex)

    def handle_error(self, failure):
        if not hasattr(failure.value, "response"):
            # We don't handle things like IgnoreRequests here
            return
        response = failure.value.response
        url = response.request.url
        status_code = response.status
        status_message = response_status_message(status_code)

        if "redirect_urls" in response.request.meta:
            # Set URL to the original URL, not the URL after redirection
            url = response.request.meta["redirect_urls"][0]

        log.msg("Handle Error: %d %s" % (status_code, url))

        # Add broken URL
        broken_url = Url(url=url, scan=self.scanner.scan_object,
                         status_code=status_code,
                         status_message=status_message)
        broken_url.save()

    def scan(self, response):
        """Scan a response, returning any matches."""

        content_type = response.headers.get('content-type')
        if content_type:
            mime_type = parse_content_type(content_type)
            log.msg("Content-Type: " + content_type, level=log.DEBUG)
        else:
            log.msg("Guessing mime-type based on file extension",
                    level=log.DEBUG)
            mime_type, encoding = mimetypes.guess_type(response.url)
            # Scrapy already guesses the encoding.. we don't need it

        if hasattr(response, "encoding"):
            try:
                data = response.body.decode(response.encoding)
            except UnicodeDecodeError, e:
                try:
                    # Encoding specified in Content-Type header was wrong, try
                    # to detect the encoding and decode again
                    encoding = chardet.detect(response.body).get('encoding')
                    if encoding is not None:
                        data = response.body.decode(encoding)
                        log.msg(("Error decoding response as %s. " +
                                 "Detected the encoding as %s.") % (
                                    response.encoding, encoding))
                    else:
                        mime_type = self.magic.from_buffer(response.body)
                        data = response.body
                        log.msg(("Error decoding response as %s. " +
                                 "Detected the mime " +
                                 "type as %s.") % (response.encoding,
                                                   mime_type))
                except UnicodeDecodeError, e:
                    # Could not decode with the detected encoding, so assume
                    # the file is binary and try to guess the mimetype from
                    # the file
                    mime_type = self.magic.from_buffer(response.body)
                    data = response.body
                    log.msg(
                        ("Error decoding response as %s. Detected the "
                         "mime type as %s.") % (response.encoding,
                                                mime_type)
                    )

        else:
            data = response.body

        # Save the URL item to the database
        if (Processor.mimetype_to_processor_type(mime_type) == 'ocr' and not
            self.scanner.scanner_object.do_ocr):
            # Ignore this URL
            return
        url_object = Url(url=response.request.url, mime_type=mime_type,
                         scan=self.scanner.scan_object)
        url_object.save()
        result = self.scanner.scan(data, url_object)


def parse_content_type(content_type):
    """Return the mime-type from the given "Content-Type" header value."""
    m = re.search('([^/]+/[^;\s]+)', content_type)
    return m.group(1)
