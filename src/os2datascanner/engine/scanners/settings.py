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
"""Scrapy settings for scanner project."""

# Scrapy settings for scanner project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
# http://doc.scrapy.org/en/latest/topics/settings.html
#
import os

BOT_NAME = 'scanners'

SPIDER_MODULES = ['os2datascanner.engine.scanners.spiders']
NEWSPIDER_MODULE = 'os2datascanner.engine.scanners.spiders'

SPIDER_MIDDLEWARES = {
    # Disable default OffsiteMiddleware
    'scrapy.spidermiddlewares.offsite.OffsiteMiddleware': None,

    # Use our own custom OffsiteMiddleware which doesn't allow subdomains
    'os2datascanner.engine.scanners.middlewares.middlewares.NoSubdomainOffsiteMiddleware': 500,

    'os2datascanner.engine.scanners.middlewares.middlewares.ExclusionRuleMiddleware': 1000,
    'os2datascanner.engine.scanners.middlewares.middlewares.LastModifiedLinkStorageMiddleware': 1100
}

COOKIES_ENABLED = True
COOKIES_DEBUG = True

DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': None,
    'os2datascanner.engine.scanners.middlewares.middlewares.OffsiteRedirectMiddleware': 600,
    'os2datascanner.engine.scanners.middlewares.middlewares.CookieCollectorMiddleware': 700,
    'os2datascanner.engine.scanners.middlewares.middlewares.OffsiteDownloaderMiddleware': 1000,
    'os2datascanner.engine.scanners.middlewares.middlewares.ExclusionRuleDownloaderMiddleware': 1100,
    'os2datascanner.engine.scanners.middlewares.webscan_middleware.WebScanLastModifiedCheckMiddleware': 1200,
}

LOG_LEVEL = 'DEBUG'

# Crawl responsibly by identifying yourself (and your website) on the
# user-agent
USER_AGENT = 'OS2Webscanner'

# Ignore Robots.txt:
#   This is the default in Scrapy, but we are explicit here just in case they
#   ever change it.
ROBOTSTXT_OBEY = False

WEBSERVICE_ENABLED = False

TELNETCONSOLE_ENABLED = True

local_settings_file = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'local_settings.py'
)
if os.path.exists(local_settings_file):
    from local_settings import *  # noqa
