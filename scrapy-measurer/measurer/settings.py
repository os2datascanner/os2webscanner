# -*- coding: utf-8 -*-

import os

# Scrapy settings for measurer project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'os2webscanner-measurer'

SPIDER_MODULES = ['measurer.spiders']
NEWSPIDER_MODULE = 'measurer.spiders'

EXTENSIONS = {
    'measurer.extensions.MeasuringExtension': 600
}

USER_AGENT = 'os2webscanner-measurer (+http://webscanner.magenta-aps.dk)'

LOG_LEVEL = 'INFO'

# Set up some directories
SETTINGS_FILE = os.path.abspath(__file__)
MEASURER_DIR = os.path.dirname(os.path.dirname(SETTINGS_FILE))
OS2_DIR = os.path.dirname(MEASURER_DIR)
VAR_DIR = os.path.join(OS2_DIR, 'var')

# Add the scrapy-webscanner files to the system path
os.sys.path.append(os.path.join(OS2_DIR,'scrapy-webscanner'))

# Create a Django settings module with the neccessary config to load
# the processor classes.
from django.conf import settings
settings.configure(
    DO_USE_GROUPS=False,
    BASE_DIR=os.path.join(OS2_DIR, 'webscanner_site'),
    VAR_DIR=VAR_DIR
)
