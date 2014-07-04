"""Scrapy settings for scanner project."""

# Scrapy settings for scanner project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
# http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'scanner'

SPIDER_MODULES = ['scanner.spiders']
NEWSPIDER_MODULE = 'scanner.spiders'

SPIDER_MIDDLEWARES = {
    # Disable default OffsiteMiddleware
    'scrapy.contrib.spidermiddleware.offsite.OffsiteMiddleware': None,

    # Use our own custom OffsiteMiddleware which doesn't allow subdomains
    'scanner.middlewares.NoSubdomainOffsiteMiddleware': 500,

    'scanner.middlewares.ExclusionRuleMiddleware': 1000,
}

DOWNLOADER_MIDDLEWARES = {
    'scrapy.contrib.downloadermiddleware.redirect.RedirectMiddleware': None,
    'scanner.middlewares.OffsiteRedirectMiddleware': 600,
}

# Set to True in testing to avoid pegging websites, if only testing processing
# MUST BE REMOVED IN PRODUCTION!!
HTTPCACHE_ENABLED = False

# Crawl responsibly by identifying yourself (and your website) on the
# user-agent
USER_AGENT = 'OS2Webscanner'

# Ignore Robots.txt:
#   This is the default in Scrapy, but we are explicit here just in case they
#   ever change it.
ROBOTSTXT_OBEY = False
