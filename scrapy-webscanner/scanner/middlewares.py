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
"""Middleware for the scanner."""
import re

from scrapy import Request
from scrapy import log
from scrapy.contrib.downloadermiddleware.redirect import RedirectMiddleware
from scrapy.contrib.spidermiddleware.offsite import OffsiteMiddleware
import scrapy.contrib.spidermiddleware.httperror
from scrapy.exceptions import IgnoreRequest
from scrapy.utils.httpobj import urlparse_cached


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
                    log.msg("Excluding %s" % x.url)
            else:
                yield x

    def should_follow(self, request, spider):
        """Return whether the URL should be followed."""
        if not hasattr(self, 'exclusion_rules'):
            self.exclusion_rules = getattr(spider, 'exclusion_rules', None)

        if self.exclusion_rules is None:
            return True

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
                    return False
            else:
                # Do regex search against the URL
                if rule.search(match_against) is not None:
                    return False
        return True


class NoSubdomainOffsiteMiddleware(OffsiteMiddleware):

    """Offsite middleware which doesn't allow subdomains of allowed_domains."""

    def get_host_regex(self, spider):
        """Disallow subdomains of the allowed domains.

        Overrides OffsiteMiddleware.
        """
        return spider.get_host_regex()


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
                    log.msg("Excluding redirect due to exclusion rule %s" %
                            result.url)
                    raise IgnoreRequest
            else:
                log.msg("Excluding redirect due to no offsite domains %s" %
                        result.url)
                raise IgnoreRequest
        else:
            return result


class LastModifiedCheckMiddleware(object):

    """Check the Last-Modified header to filter responses.

    Only process a response if the content for the URL has been updated as
    indicated by the Last-Modified header.

    Optionally, change GET requests into HEAD requests (to avoid
    transferring too much data before we know if a URL has been updated),
    then check the Last-Modified header before issuing a new request.

    Last-modified dates are stored in the database."""

    def process_request(self, request, spider):
        """Process a spider request."""
        # Make the request into a HEAD request instead of a GET request,
        # if the spider says we should and if we haven't
        # already checked the last modified date.
        if (getattr(spider, 'do_last_modified_check', False) and
                getattr(spider, 'do_last_modified_check_head_request', True)
                and not request.meta.get('skip_modified_check', False) and
                request.method != "HEAD"):
            log.msg("Replacing with HEAD request %s" % request)
            return request.replace(method='HEAD')
        else:
            log.msg("process_request %s" % request)
            return None

    def process_response(self, request, response, spider):
        """Process a spider response."""
        # Don't run the check if it's not specified by the spider
        log.msg("process_response %s" % response)
        if not getattr(spider, 'do_last_modified_check', False):
            return response

        # We only handle HTTP status OK responses
        # TODO: Is this correct?
        if response.status != 200:
            return response

        # Check the Last-Modified header to see if the content has been
        # updated since the last time we checked it.
        if self.has_been_modified(response):
            if request.method == 'HEAD':
                # Issue a new GET request, since the data was updated
                log.msg("Issuing a new GET for %s" % request)

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
            # Ignore the response, since the content has not been modified
            raise IgnoreRequest

    def process_exception(self, request, exception, spider):
        log.msg("process_exception %s %s %s" % (request, exception, spider))

    def has_been_modified(self, response):
        """Return whether the given response has been modified since we
        last saw it.

        We check against the database here."""
        # Check the Last-Modified header to see if the content has been
        # updated since the last time we checked it.
        last_modified_header = response.headers.get("Last-Modified", None)
        log.msg("Last modified header: %s" % last_modified_header)
        if last_modified_header is not None:
            # TODO: Check against the database
            is_updated = True
            # TODO: Update last-modified date in the database
            return is_updated
        else:
            # If there is no Last-Modified header, we have to assume it has
            # been modified.
            return True
