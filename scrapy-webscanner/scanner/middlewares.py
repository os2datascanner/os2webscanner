"""Middleware for the scanner."""

from scrapy import Request
from scrapy import log
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
        exclusion_rules = getattr(spider, 'exclusion_rules', None)
        for x in result:
            if isinstance(x, Request):
                if exclusion_rules is not None:
                    if self.should_follow(x, exclusion_rules):
                        yield x
                    else:
                        # TODO: Log excluded URLs somewhere?
                        log.msg("Excluding %s" % x.url, level=log.DEBUG)
            else:
                yield x

    def should_follow(self, request, exclusion_rules):
        """Return whether the URL should be followed."""
        # Build a string to match against, containing the path, and if
        # present, the query and fragment as well.
        url = urlparse_cached(request)
        match_against = url.path
        if url.query != '':
            match_against += "?" + url.query
        if url.fragment != '':
            match_against += "#" + url.fragment

        for rule in exclusion_rules:
            if isinstance(rule, basestring):
                # Do case-insensitive substring search
                if match_against.lower().find(rule.lower()) != -1:
                    return False
            else:
                # Do regex search against the URL
                if rule.search(match_against) is not None:
                    return False
        return True