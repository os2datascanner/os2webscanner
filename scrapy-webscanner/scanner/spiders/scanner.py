from scrapy import log
from scrapy.contrib.spiders.sitemap import SitemapSpider

from followall import FollowAllSpider
from ..processors import html
import re

from ..rules.name import NameRule
from ..rules.cpr import CPRRule

import mimetypes


def parse_content_type(content_type):
    """Parse the mimetype from a Content-Type header value
    :param content_type:
    :return: mime type
    """
    m = re.search('([^/]+/[^;\s]+)', content_type)
    return m.group(1)

class ScannerSpider(FollowAllSpider, SitemapSpider):
    name = 'scanner'
    processors = {
        # 'application/pdf': pdf2html,
        'text/html': html.HTMLProcessor(),
    }

    def __init__(self, sitemap_urls, allowed_domains, *a, **kw):
        self.sitemap_urls = sitemap_urls
        self.sitemap_alternate_links = True
        FollowAllSpider.__init__(self, *a, **kw)
        SitemapSpider.__init__(self, *a, **kw)

        # TODO: Load from settings
        self.allowed_domains.extend(allowed_domains)

        # TODO: Pass arguments to rules based on settings
        # TODO: Add Regex Rules
        self._rules = [CPRRule(), NameRule()]

    def start_requests(self):
        # Follow all links found in the starting URLs AND sitemap URLs
        requests = FollowAllSpider.start_requests(self)
        requests.extend(list(SitemapSpider.start_requests(self)))
        return requests

    def scan(self, response):
        # Get the mime-type from the Content-Type header or the file extension
        content_type = response.headers.get('content-type')
        if content_type:
            mime_type = parse_content_type(content_type)
            log.msg("Content-Type: " + content_type, level=log.DEBUG)
        else:
            log.msg("Guessing mime-type based on file extension", level=log.DEBUG)
            mime_type = mimetypes.guess_type(response.url)
            if mime_type is None:
                mime_type = 'text/plain'

        log.msg("Scanning " + response.url + " Mime-type: " + mime_type)
        processor = self.processors.get(mime_type, None)
        matches = []
        if processor is not None:
            if callable(processor.process):
                log.msg("Processing with " + processor.__class__.__name__)
                # Process the text (for example to remove HTML, or add to conversion queue)
                text = processor.process(response)
                # TODO: Check if the processor only adds it to the conversion queue
                matches = self.execute_rules(text)
            else:
                raise Exception("Processor lacks process method")
        else:
            log.msg("No processor available for mime type: " + mime_type)
        return matches

    def execute_rules(self, text):
        matches = []
        for rule in self._rules:
            rule_matches = rule.execute(text)
            # TODO: Associate the URL and scan with each match
            for match in rule_matches:
                match['matched_rule'] = rule.name
            matches.extend(rule_matches)
        return matches

    def rules(self):
        return self._rules