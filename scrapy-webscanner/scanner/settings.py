# Scrapy settings for os2scanner project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'scanner'

SPIDER_MODULES = ['scanner.spiders']
NEWSPIDER_MODULE = 'scanner.spiders'

# Set to True in testing to avoid pegging websites, if only testing processing
# MUST BE REMOVED IN PRODUCTION!!
HTTPCACHE_ENABLED = True

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'os2webscanner'

# Ignore Robots.txt:
#   This is the default in Scrapy, but we are explicit here just in case they
#   ever change it.
ROBOTSTXT_OBEY=False