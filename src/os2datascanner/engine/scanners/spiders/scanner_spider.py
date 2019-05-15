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
import logging
import magic
import mimetypes
import re
import regex

from magic import MagicException

from .base_spider import BaseScannerSpider

from ..processors.processor import Processor

from os2datascanner.sites.admin.adminapp.utils import capitalize_first, get_codec_and_string
from os2datascanner.sites.admin.adminapp.models.url_model import Url


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

        self.crawl = False

        self.setup_spider()

    def setup_spider(self):
        raise NotImplementedError

    def start_requests(self):
        """Return requests for all starting URLs AND sitemap URLs."""
        raise NotImplementedError

    def parse(self, response):
        """Process a response and follow all links."""
        raise NotImplementedError

    def handle_error(self, failure):
        """Handle an error due to a non-success status code or other reason.

        If link checking is enabled, saves the broken URL and referrers.
        """
        raise NotImplementedError

    def broken_url_save(self, status_code, status_message, url):
        logging.info("Handle Error: %s %s" % (status_message, url))
        status_message = regex.sub("\[.+\] ", "", status_message)
        status_message = capitalize_first(status_message)
        # Add broken URL
        return self.scanner.mint_url(
            url=url, status_code=status_code, status_message=status_message)

    def scan(self, response):
        """Scan a response, returning any matches."""

        mime_type = self.get_mime_type(response)

        # Save the URL item to the database
        if (Processor.mimetype_to_processor_type(mime_type) == 'ocr'
            and not self.scanner.do_ocr):
            # Ignore this URL
            return

        url_object = self.url_save(mime_type,
                                   response.request.url)

        data = response.body

        self.scanner.scan(data, url_object)

    def url_save(self, mime_type, url):
        return self.scanner.mint_url(url=url, mime_type=mime_type)

    def get_mime_type(self, response):
        content_type = response.headers.get('content-type')
        if content_type:
            mime_type = parse_content_type(content_type)
        else:
            mime_type, encoding = mimetypes.guess_type(response.url)
            if not mime_type:
                try:
                    mime_type = self.magic.from_buffer(response.body)
                except MagicException as me:
                    logging.error(me)

        return mime_type

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
