import logging
import datetime
import dateutil.tz
import arrow

from lxml import html
from email.utils import parsedate_tz, mktime_tz

from scrapy import Request
from scrapy.exceptions import IgnoreRequest
from scrapy.utils.url import canonicalize_url

from os2datascanner.sites.admin.adminapp.models.urllastmodified_model import UrlLastModified

from .middlewares import LastModifiedCheckMiddleware


class WebScanLastModifiedCheckMiddleware(LastModifiedCheckMiddleware):

    def __init__(self, crawler):
        super().__init__(crawler)

    def process_request(self, request, spider):
        """Process a spider request."""
        # Make the request into a HEAD request instead of a GET request,
        # if the spider says we should and if we haven't
        # already checked the last modified date.
        if (spider.scanner.do_last_modified_check_head_request
            and not request.meta.get('skip_modified_check', False) and
                    request.method != "HEAD" and
                    self.get_stored_last_modified_date(request.url, spider) is not
                    None):
            logging.debug("Replacing with HEAD request %s" % request)
            return request.replace(method='HEAD')
        else:
            return None

    def process_response(self, request, response, spider):
        """Process a spider response."""
        logging.info("Process response for url {}".format(request.url))
        # Don't run the check if it's not specified by the spider...
        if request.meta.get('skip_modified_check', False):
            return response
        # ... or by the scanner
        if not spider.scanner.do_last_modified_check:
            return response
        # We only handle HTTP status OK responses
        if response.status != 200:
            return response

        # Check the Last-Modified header to see if the content has been
        # updated since the last time we checked it.
        if self.has_been_modified(request, response, spider):
            logging.debug("Page has been modified since Last-Modified {}".format(response))
            # request.method only available for webscanner
            if request.method == 'HEAD':
                # Issue a new GET request, since the data was updated
                logging.debug("Issuing a new GET for {}".format(request))

                # Skip the modified check, since we just did the check
                meta = request.meta
                meta["skip_modified_check"] = True

                # Have to pass dont_filter=True or the request will be
                # filtered by the duplicates filter (since it was originally
                # scheduled as a GET request already).
                return request.replace(method='GET', dont_filter=True)
            else:
                # If it's a GET request, process the response
                return response
        else:
            # Add requests for all the links that we know were on the
            # page the last time we visited it.
            links = self.get_stored_links(response.url, spider)
            for link in links:
                req = Request(link.url,
                              callback=request.callback,
                              errback=request.errback,
                              headers={"referer": response.url})
                logging.debug("Adding request {}".format(req))
                self.crawler.engine.crawl(req, spider)
            # Ignore the request, since the content has not been modified
            self.stats.inc_value('last_modified_check/pages_skipped')
            raise IgnoreRequest

    def has_been_modified(self, request, response, spider):
        """Return whether the response was modified since last seen.

        We check against the database here.
        If the response has been modified, we update the database.
        If there is no stored last modified date, we save one.
        """
        # Check the Last-Modified header to see if the content has been
        # updated since the last time we checked it.
        last_modified_header = response.headers.get("Last-Modified", None)
        if last_modified_header is not None:
            last_modified_header_date = datetime.datetime.fromtimestamp(
                mktime_tz(parsedate_tz(last_modified_header.decode('utf-8'))),
                tz=dateutil.tz.UTC,
            )
        else:
            last_modified_header_date = None

        if last_modified_header_date is None and request.method == 'GET':
            content_type_header = response.headers.get(
                "Content-Type", None
            ).decode('utf-8')
            if content_type_header.startswith("text/html"):
                try:
                    body_html = html.fromstring(response.body)
                except Exception:
                    logging.info('Error occured while trying to extract string from response body.')

                meta_dict = {list(el.values())[0]: list(el.values())[1]
                             for el in body_html.findall('head/meta')}
                if 'last-modified' in meta_dict:
                    lm = meta_dict['last-modified']
                    try:
                        last_modified_header_date = arrow.get(lm).datetime
                    except Exception:
                        logging.error(
                            "Date format error on last modied: {0}".format(lm)
                        )

        # lastmod comes from a sitemap.xml file
        sitemap_lastmod_date = request.meta.get("lastmod", None)
        if sitemap_lastmod_date is None:
            last_modified = last_modified_header_date
            logging.debug("Using header's last-modified date: %s"
                          % last_modified)
        else:
            if last_modified_header_date is None:
                # No Last-Modified header, use the lastmod from the sitemap
                last_modified = sitemap_lastmod_date
                logging.debug("Using lastmod from sitemap %s" % last_modified)
            else:
                # Take the most recent of the two
                logging.debug("Taking most recent of (header) %sand (sitemap) %s"
                              % (last_modified_header_date,
                                 sitemap_lastmod_date))
                last_modified = max(last_modified_header_date,
                                    sitemap_lastmod_date)
                logging.debug("Last modified %s" % last_modified)

        if last_modified is not None:
            # Check against the database
            canonical_url = canonicalize_url(response.url)
            try:
                url_last_modified = UrlLastModified.objects.get(
                    url=canonical_url,
                    scanner=self.get_scanner_object(spider)
                )
                stored_last_modified = url_last_modified.last_modified
                logging.info("Comparing header %s against stored %s" % (
                    last_modified, stored_last_modified))
                if (stored_last_modified is not None
                    and last_modified == stored_last_modified):
                    return False
                else:
                    # Update last-modified date in database
                    url_last_modified.last_modified = last_modified
                    url_last_modified.save()
                    return True
            except UrlLastModified.DoesNotExist:
                logging.debug("No stored Last-Modified header found.")
                url_last_modified = UrlLastModified(
                    url=canonical_url,
                    last_modified=last_modified,
                    scanner=self.get_scanner_object(spider)
                )
                logging.debug("Saving new last-modified value {}".format(
                              url_last_modified))
                url_last_modified.save()
                return True
        else:
            # If there is no Last-Modified header, we have to assume it has
            # been modified.
            logging.debug('No Last-Modified header found at all.')
            return True

    def get_stored_links(self, url, spider):
        """Return the links that have been stored for this URL."""
        url = canonicalize_url(url)
        try:
            url_last_modified = UrlLastModified.objects.get(
                url=url, scanner=self.get_scanner_object(spider))
            return url_last_modified.links.all()
        except UrlLastModified.DoesNotExist:
            return []

    def get_stored_last_modified_date(self, url, spider):
        """Return the last modified date that has been stored for this URL."""
        url_last_modified_object = self.get_stored_last_modified_object(url,
                                                                        spider)
        if url_last_modified_object is not None:
            return url_last_modified_object.last_modified
        else:
            return None

    def get_stored_last_modified_object(self, url, spider):
        """Return the UrlLastModified object for the given URL."""
        url = canonicalize_url(url)
        try:
            url_last_modified = UrlLastModified.objects.get(
                url=url, scanner=self.get_scanner_object(spider))
            return url_last_modified
        except UrlLastModified.DoesNotExist:
            return None

    def get_scanner_object(self, spider):
        """Return the spider's scanner object."""
        return spider.scanner.scan_object.scanner

