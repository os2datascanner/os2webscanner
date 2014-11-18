"""Monkey-patch the LxmlParserLinkExtractor."""

from urlparse import urljoin

from scrapy import log
from scrapy.contrib.linkextractors.lxmlhtml import LxmlParserLinkExtractor
from scrapy.contrib.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.contrib.linkextractors.lxmlhtml import _collect_string_content
from scrapy.utils.python import unique as unique_list
from scrapy.link import Link


def _is_valid_link(url):
    """Return whether the link is valid (that we want to visit).

    No mailto, tel, etc... schemes.
    """
    parts = url.strip().split(':', 1)
    if len(parts) > 1 and parts[0] not in ('http', 'https'):
        log.msg("Ignoring link %s" % url)
        return False
    else:
        return True


def _extract_links(self, selector, response_url, response_encoding, base_url):
    links = []
    # hacky way to get the underlying lxml parsed document
    for el, attr, attr_val in self._iter_links(selector._root):
        if self.scan_tag(el.tag) and self.scan_attr(attr):
            # pseudo _root.make_links_absolute(base_url)
            # START PATCH: Added check to filter links before making absolute
            if not _is_valid_link(attr_val):
                continue
            # END PATCH
            attr_val = urljoin(base_url, attr_val)
            url = self.process_attr(attr_val)
            if url is None:
                continue
            if isinstance(url, unicode):
                url = url.encode(response_encoding)
            # to fix relative links after process_value
            url = urljoin(response_url, url)
            link = Link(
                url, _collect_string_content(el) or u'',
                nofollow=True if el.get('rel') == 'nofollow' else False
            )
            links.append(link)
    return unique_list(links, key=lambda link: link.url) \
        if self.unique else links

# Monkey-patch link extractor to ignore links with certain schemes
LxmlParserLinkExtractor._extract_links = _extract_links
