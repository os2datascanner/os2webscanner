"""
Django settings for webscanner project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
PROJECT_DIR = os.path.dirname(BASE_DIR)
VAR_DIR = os.path.join(PROJECT_DIR, 'var')
LOGS_DIR = os.path.join(VAR_DIR, 'logs')

# Site URL for calculating absolute URLs in emails.
SITE_URL = 'http://webscanner.magenta-aps.dk'

SITE_ID = 1

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'ld0_g)jhp3v27&od88-_v83ldb!0i^bac=jh+je!!=jbvra7@j'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = ['192.168.1.229']


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'os2webscanner',
    'recurrence',
    'django_xmlrpc',
)

XMLRPC_METHODS = (
    ('os2webscanner.rpc.scan_urls', 'scan_urls'),
    ('os2webscanner.rpc.scan_documents', 'scan_documents'),
    ('os2webscanner.rpc.get_status', 'get_status'),
    ('os2webscanner.rpc.get_report', 'get_report'),
)
MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'webscanner.urls'

WSGI_APPLICATION = 'webscanner.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'os2webscanner',
        'USER': 'os2webscanner',
        'PASSWORD': 'os2webscanner',
        'HOST': '127.0.0.1',
    }
}

DATABASE_POOL_ARGS = {
    'max_overflow': 10,
    'pool_size': 5,
    'recycle': 300
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'da-dk'

TIME_ZONE = 'CET'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = '/home/os2/os2webscanner/webscanner_site/static'

AUTH_PROFILE_MODULE = 'os2webscanner.UserProfile'

LOGIN_REDIRECT_URL = '/'

# Email settings

DEFAULT_FROM_EMAIL = 'carstena@magenta.dk'
ADMIN_EMAIL = 'carstena@magenta.dk'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Enable groups - or not

DO_USE_GROUPS = False

# Use MD5 sums.
# This should practically always be true, but we might want to disable it for
# debugging uses. At some point, this could also become a parameter on the
# scanner.

DO_USE_MD5 = True

# The threshold for number of OCR conversion queue items per scan above which
# non-OCR conversion will be paused. The reason to have this feature is that
# for large scans with OCR enabled, so many OCR items are extracted from
# PDFs or Office documents that it exhausts the number of available inodes
# on the filesystem. Pausing non-OCR conversions allows the OCR processors a
# chance to process their queue items to below a reasonable level.
PAUSE_NON_OCR_ITEMS_THRESHOLD = 2000

# The threshold for number of OCR conversion queue items per scan below which
# non-OCR conversion will be resumed. This must be a lower number than
# PAUSE_NON_OCR_ITEMS_THRESHOLD.
RESUME_NON_OCR_ITEMS_THRESHOLD = PAUSE_NON_OCR_ITEMS_THRESHOLD - 1000

# Directory to store files transmitted by RPC
RPC_TMP_PREFIX = '/tmp/os2webscanner'

# Always store temp files on disk
FILE_UPLOAD_MAX_MEMORY_SIZE = 0

local_settings_file = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'local_settings.py'
)
if os.path.exists(local_settings_file):
    from local_settings import *
