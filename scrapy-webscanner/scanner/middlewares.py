"""Middleware for the scanner."""
import re

from scrapy import Request
from scrapy import log
from scrapy.contrib.downloadermiddleware.redirect import RedirectMiddleware
from scrapy.contrib.spidermiddleware.offsite import OffsiteMiddleware
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
        allowed_domains = getattr(spider, 'allowed_domains', None)
        if not allowed_domains:
            return re.compile('')  # allow all by default
        regex = r'^(www\.)?(%s)$' % '|'.join(re.escape(d) for d in
                                             allowed_domains
                                             if d is not None)
        return re.compile(regex)


class OffsiteRedirectMiddleware(RedirectMiddleware,
                                NoSubdomainOffsiteMiddleware,
                                ExclusionRuleMiddleware):
    """Handle redirects but make sure they are not offsite and not on the
    exclusion list."""

    def process_response(self, request, response, spider):
        if not hasattr(self, 'host_regex'):
            self.host_regex = self.get_host_regex(spider)
        result = RedirectMiddleware.process_response(self,
                                                     request, response, spider)
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
