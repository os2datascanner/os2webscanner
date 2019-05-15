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
# OS2Webscanner was developed by Magenta n collaboration with OS2 the
# Danish community of open source municipalities (http://www.os2web.dk/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( http://www.os2web.dk/ )
"""Middleware for the scanner."""

import logging

from scrapy import Request
from scrapy import signals

from scrapy.downloadermiddlewares.redirect import RedirectMiddleware
from scrapy.downloadermiddlewares.cookies import CookiesMiddleware
from scrapy.spidermiddlewares.offsite import OffsiteMiddleware
from scrapy.exceptions import IgnoreRequest
from scrapy.utils.httpobj import urlparse_cached
from scrapy.utils.url import canonicalize_url


from os2webscanner.models.urllastmodified_model import UrlLastModified

from django.conf import settings as django_settings


class ExclusionRuleMiddleware(object):

    """A Spider Middleware which excludes certain URLs from being followed.

    If the spider has an exclusion_rules attribute, this is used to determine
    whether to visit the URLs.
    The exclusion_rules is a list which can be either strings or compiled
    regular expressions.
    """

    def process_spider_output(self, response, result, spider):
        """Process the output of a spider."""
        for x in result:
            if isinstance(x, Request):
                if self.should_follow(x, spider):
                    yield x
                else:
                    # TODO: Log excluded URLs somewhere?
                    logging.info("Excluding %s" % x.url)
            else:
                yield x

    def should_follow(self, request, spider):
        """Return whether the URL should be followed."""
        return not spider.is_excluded(request)


class NoSubdomainOffsiteMiddleware(OffsiteMiddleware):

    """Offsite middleware which doesn't allow subdomains of allowed_domains."""

    def get_host_regex(self, spider):
        """Disallow subdomains of the allowed domains.

        Overrides OffsiteMiddleware.
        """
        return spider.get_host_regex()


class CookieCollectorMiddleware(CookiesMiddleware):

    """Collect all cookies set while scanning."""

    def process_response(self, request, response, spider):

        """Collect cookie, store on scan object."""

        # First, extract cookies as needed - call superclass.
        response = super().process_response(request, response, spider)

        # Now collect cookie
        current_scan = spider.scanner.scan_object
        domain = urlparse_cached(request).hostname
        if current_scan.webscan.do_collect_cookies:

            for cookie in response.headers.getlist('Set-Cookie'):
                current_scan.logging_cookie(domain + '|' + cookie)

        return response


class OffsiteDownloaderMiddleware(object):

    """Offsite middleware which doesn't allow subdomains of allowed_domains."""

    @classmethod
    def from_crawler(cls, crawler):
        """Connect spider open signal."""
        o = cls()
        crawler.signals.connect(o.spider_opened, signal=signals.spider_opened)
        return o

    def process_request(self, request, spider):
        """Process a spider request."""
        if request.dont_filter or self.should_follow(request, spider):
            return None
        else:
            domain = urlparse_cached(request).hostname
            logging.debug("Filtered offsite request to %(domain)r: %(request)s" %
                          {"domain": domain, "request": request})
            raise IgnoreRequest

    def should_follow(self, request, spider):
        """Return whether the request should be followed."""
        regex = self.host_regex
        # hostname can be None for wrong urls (like javascript links)
        parse_result = urlparse_cached(request)
        host = parse_result.hostname or ''
        scheme = parse_result.scheme or ''
        # XMLRPC call
        if scheme == 'file' and not getattr(spider, "crawl", False):
            return parse_result.path.startswith(django_settings.RPC_TMP_PREFIX)
        # File scanner
        elif scheme == 'file' and getattr(spider, "crawl", True):
            return True
        return bool(regex.search(host))

    def get_host_regex(self, spider):
        """Return the regex which hosts should be matched against."""
        return spider.get_host_regex()

    def spider_opened(self, spider):
        """Store the spider's host regex."""
        self.host_regex = self.get_host_regex(spider)


class ExclusionRuleDownloaderMiddleware(object):

    """Exclusion rule downloader middleware."""

    def process_request(self, request, spider):
        """Process a spider request."""
        if request.dont_filter or self.should_follow(request, spider):
            return None
        else:
            raise IgnoreRequest

    def should_follow(self, request, spider):
        """Return whether the request should be followed (not excluded)."""
        return not spider.is_excluded(request)


class OffsiteRedirectMiddleware(RedirectMiddleware,
                                NoSubdomainOffsiteMiddleware,
                                ExclusionRuleMiddleware):

    """Handle redirects, ensuring they are not offsite or excluded URLs."""

    def process_response(self, request, response, spider):
        """Process a spider response."""
        if not hasattr(self, 'host_regex'):
            self.host_regex = self.get_host_regex(spider)
        result = RedirectMiddleware.process_response(
            self, request, response, spider
        )
        if isinstance(result, Request):
            # Check that the redirect request is not offsite
            if NoSubdomainOffsiteMiddleware.should_follow(self, result,
                                                          spider):
                if ExclusionRuleMiddleware.should_follow(self, result,
                                                         spider):
                    return result
                else:
                    logging.info("Excluding redirect due to exclusion rule %s" %
                                result.url)
                    raise IgnoreRequest
            else:
                logging.info("Excluding redirect due to no offsite domains %s" %
                            result.url)
                raise IgnoreRequest
        else:
            return result


class LastModifiedLinkStorageMiddleware(object):

    """Spider middleware to store links on pages for Last-Modified check."""

    def process_spider_output(self, response, result, spider):
        """Process spider output."""
        if not spider.scanner.do_last_modified_check:
            return result
        last_modified_header = response.headers.get("Last-Modified", None)
        if last_modified_header is None:
            # We don't need to store the links, since the page has no
            # Last-Modified header.
            return result

        source_url = canonicalize_url(response.request.url)
        try:
            url_last_modified = UrlLastModified.objects.get(
                url=source_url,
                scanner=self.get_scanner_object(spider)
            )
        except UrlLastModified.DoesNotExist:
            # We never stored the URL for the original request: this
            # shouldn't happen.
            logging.exception(
                "no original last modification for URL %s in %s",
                source_url,
                self.get_scanner_object(spider),
            )

            return result

        logging.debug("Updating links for %s" % url_last_modified)

        # Clear existing links
        url_last_modified.links.clear()

        # Update links
        for r in result:
            if isinstance(r, Request):
                if spider.is_offsite(r) or spider.is_excluded(r):
                    continue
                target_url = canonicalize_url(r.url)
                # Get or create a URL last modified object
                link, created = UrlLastModified.objects.get_or_create(
                    url=target_url,
                    scanner=self.get_scanner_object(spider),
                )

                # Add the link to the URL last modified object
                url_last_modified.links.add(link)
                logging.debug("Added link %s" % link)
        return result

    def get_scanner_object(self, spider):
        """Return the spider's scanner object."""
        return spider.scanner.scan_object.scanner


class LastModifiedCheckMiddleware(object):

    """Check the Last-Modified header to filter responses.

    Only process a response if the content for the URL has been updated as
    indicated by the Last-Modified header.

    Optionally, change GET requests into HEAD requests (to avoid
    transferring too much data before we know if a URL has been updated),
    then check the Last-Modified header before issuing a new request.

    Last-modified dates are stored in the database.
    """

    def __init__(self, crawler):
        """Initialize the middleware."""
        self.crawler = crawler
        self.stats = crawler.stats

    @classmethod
    def from_crawler(cls, crawler):
        """Instantiate the middleware."""
        return cls(crawler)

    def process_request(self, request, spider):
        """Process a spider request."""
        raise NotImplementedError

    def process_response(self, request, response, spider):
        """Process a spider response."""
        raise NotImplementedError

    def has_been_modified(self, request, response, spider):
        """Return whether the response was modified since last seen.

        We check against the database here.
        If the response has been modified, we update the database.
        If there is no stored last modified date, we save one.
        """
        raise NotImplementedError
