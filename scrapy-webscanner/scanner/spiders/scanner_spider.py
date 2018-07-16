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
import chardet
import errno
import logging
import magic
import mimetypes
import os
from os import walk
import re
import regex

from scrapy.spidermiddlewares.httperror import HttpError
from scrapy.exceptions import IgnoreRequest
from scrapy.http import Request, HtmlResponse, TextResponse
from scrapy.utils.response import response_status_message

# Use our monkey-patched link extractor
from ..linkextractor import LxmlLinkExtractor

from .base_spider import BaseScannerSpider

from ..processors.processor import Processor

from os2webscanner.utils import capitalize_first
from os2webscanner.models.url_model import Url
from os2webscanner.models.referrerurl_model import ReferrerUrl


class ScannerSpider(BaseScannerSpider):

    """A spider which uses a scanner to scan all data it comes across."""

    name = 'scanner'
    magic = magic.Magic(mime=True)

    def __init__(self, scanner, runner, *a, **kw):
        """Initialize the ScannerSpider with a Scanner object.

        The configuration will be loaded from the Scanner.
        """
        super().__init__(scanner=scanner, *a, **kw)

        self.runner = runner

        self.start_urls = []

        self.setup_spider()

    def setup_spider(self):
        scan_object = self.scanner.scan_object
        # If the scan is run from a web service, use the starting urls
        if scan_object.scanner.process_urls:
            # from the scanner.
            self.start_urls = scan_object.scanner.process_urls
            self.crawl = False
        else:
            self.crawl = True
            # Otherwise, use the roots of the domains as starting URLs
            logging.info("Initializing spider")
            if hasattr(scan_object, 'webscan'):
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
                self.do_last_modified_check = getattr(
                    scan_object.webscan, "do_last_modified_check"
                )
                self.do_last_modified_check_head_request = getattr(
                    scan_object.webscan, "do_last_modified_check_head_request"
                )
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
            elif hasattr(scan_object, 'filescan'):
                for path in self.allowed_domains:
                    logging.info("Start path %s" % str(path))
                    if not path.startswith('file://'):
                        path = 'file://%s' % path

                    self.start_urls.append(path)

                self.do_last_modified_check = getattr(
                    scan_object.filescan, "do_last_modified_check"
                )
                # Not used on type filescan
                self.do_last_modified_check_head_request = False

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

        for url in self.start_urls:
            if hasattr(self.scanner.scan_object, 'filescan'):
                # Some of the files are directories. We handle them in handle_error method.
                requests.extend(self.append_file_request(url))

            else:
                requests.append(Request(url, callback=self.parse,
                                         errback=self.handle_error))
        return requests

    def parse(self, response):
        """Process a response and follow all links."""
        if self.crawl:
            requests = self._extract_requests(response)
        else:
            requests = []

        self.scan(response)

        if self.scanner.scan_object.webscan.do_link_check:
            source_url = response.request.url
            for request in requests:
                target_url = request.url
                self.referrers.setdefault(target_url, []).append(source_url)
                if (self.scanner.scan_object.webscan.do_external_link_check and
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
        r = []
        links = self.link_extractor.extract_links(response)
        r.extend(Request(x.url, callback=self.parse,
                         errback=self.handle_error) for x in links)
        return r

    def file_extractor(self, filepath):
        """
        Generate sitemap for filescan using walk dir path
        :param filepath: The path to the files
        :return: filemap
        """
        path = filepath.replace('file://', '')
        filemap = []
        if os.path.isdir(path) is not True:
            return filemap
        for (dirpath, dirnames, filenames) in walk(path):
            for filename in filenames:
                filename = filepath + '/' + filename
                filemap.append(filename)
            for dirname in dirnames:
                dirname = filepath + '/' + dirname
                filemap.append(dirname)
            break;

        return filemap

    def handle_error(self, failure):
        """Handle an error due to a non-success status code or other reason.

        If link checking is enabled, saves the broken URL and referrers.
        """
        # If scanner is type filescan
        if hasattr(self.scanner.scan_object, 'filescan'):
            # If file is a directory loop through files within
            if isinstance(failure.value, IOError) \
                    and failure.value.errno == errno.EISDIR:
                logging.debug('File that is failing: {0}'.format(failure.value.filename))

                return self.append_file_request('file://' + failure.value.filename)
            # If file has not been changes since last, an ignorerequest is returned.
            elif isinstance(failure.value, IgnoreRequest):
                return
        # Else if scanner is type webscan
        elif hasattr(self.scanner.scan_object, 'webscan'):
            # If we should not do link check or failure is ignore request
            # and it is not a http error we know it is a last-modified check.
            if (not self.scanner.scan_object.webscan.do_link_check or
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

    def append_file_request(self, url):
        files = self.file_extractor(url)
        requests = []
        for file in files:
            try:
                requests.append(Request(file, callback=self.scan,
                                        errback=self.handle_error))
            except UnicodeEncodeError as uee:
                logging.error('UnicodeEncodeError in handle error method: {0}'.format(uee))
                logging.error('Error happened for file: {0}'.format(file))
        return requests

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
                url=referrer, scan=self.scanner.scan_object.webscan)
            self.referrer_url_objects[referrer].save()
        return self.referrer_url_objects[referrer]

    def scan(self, response):
        """Scan a response, returning any matches."""
        logging.info('Stats: {0}'.format(self.crawler.stats.get_stats()))

        content_type = response.headers.get('content-type')
        if content_type:
            mime_type = parse_content_type(content_type)
        else:
            mime_type, encoding = mimetypes.guess_type(response.url)
            if not mime_type:
                mime_type = self.magic.from_buffer(response.body)

        data, mime_type = self.check_encoding(mime_type, response)

        # Save the URL item to the database
        if (Processor.mimetype_to_processor_type(mime_type) == 'ocr'
            and not self.scanner.scan_object.do_ocr):
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
