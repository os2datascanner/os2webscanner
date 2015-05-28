# -*- coding: utf-8 -*-
import scrapy
import re
import os
from scrapy.contrib.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.http import Request, HtmlResponse
from measurer.items import MeasurerItem

class MeasuringSpider(scrapy.Spider):
    name = "measuring-spider"

    def __init__(self, *a, **kw):
        """Setup the start URL for the measuring spider.
        """
        start_url = kw['start_url'] if 'start_url' in kw else None
        if start_url is None:
            os.sys.stderr.write(
                "\nYou must specify a start url using\n\n" +
                " scrapy crawl -a start_url='<start_url>' measuring-spider" +
                "\n\n"
            )
            os.sys.exit(1)

        super(MeasuringSpider, self).__init__(*a, **kw)

        self.start_urls = [ start_url ]
        start_domain = re.sub("^https?://", "", start_url)
        start_domain = re.sub("/.*$", "", start_domain);
        self.allowed_domains = [ start_domain ]

        self.link_extractor = LxmlLinkExtractor(
            deny_extensions=(),
            tags=('a', 'area', 'frame', 'iframe', 'script'),
            attrs=('href', 'src')
        )

    def parse(self, response):
        self.log('A response from %s just arrived!' % response.url)

        item = MeasurerItem()
        content_type = response.headers.get('content-type')
        if content_type:
            item['mimetype'] = parse_content_type(content_type)
        else:
            item['mimetype'] = 'application/octet-stream'
        item.set_content(response.body)
        fname = os.path.basename(response.url)
        if fname == '':
            fname = "dummy.data"
        item['filename'] = fname

        r = [item]

        if isinstance(response, HtmlResponse):
            links = self.link_extractor.extract_links(response)
            # log.msg("Extracted links: %s" % links, level=log.DEBUG)
            r.extend(Request(x.url, callback=self.parse) for x in links)

        return r

def parse_content_type(content_type):
    """Return the mime-type from the given "Content-Type" header value."""
    m = re.search('([^/]+/[^;\s]+)', content_type)
    return m.group(1)
