"""
Django settings for webscanner project.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import pathlib
import os

import structlog

from django.utils.translation import gettext_lazy as _


BASE_DIR = str(pathlib.Path(__file__).resolve().parent.parent.parent.parent.absolute())
PROJECT_DIR = os.path.dirname(BASE_DIR)
BUILD_DIR = os.path.join(PROJECT_DIR, 'build')
VAR_DIR = os.path.join(PROJECT_DIR, 'var')
LOGS_DIR = os.path.join(VAR_DIR, 'logs')

os.makedirs(BUILD_DIR, exist_ok=True)

# Local settings file shall be used for debugging.
DEBUG = False

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django_settings_export.settings_export',
            ],
        },
    },
]

# Site URL for calculating absolute URLs in emails.
SITE_URL = 'http://webscanner.magenta-aps.dk'

SITE_ID = 1

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'ld0_g)jhp3v27&od88-_v83ldb!0i^bac=jh+je!!=jbvra7@j'

# Used for filescan and mounting
PRODUCTION_MODE = False

# If webscan on the current installation is needed, enable it here
ENABLE_WEBSCAN = True

# If filescan on the current installation is needed, enable it here
ENABLE_FILESCAN = True

# If exchangescan on the current installation is needed, enable it here
ENABLE_EXCHANGESCAN = True

# Check for dead scanner processes at this interval, in seconds
CHECK_SCAN_INTERVAL = 300

# Purge scanner queue items at this interval, in seconds
CLEANUP_SCAN_INTERVAL = 300

# Add settings here to make them accessible from templates
SETTINGS_EXPORT = [
    'DEBUG',
    'ENABLE_FILESCAN',
    'ENABLE_EXCHANGESCAN',
    'ENABLE_WEBSCAN',
    'ICON_SPRITE_URL'
]

TEST_RUNNER = 'xmlrunner.extra.djangotestrunner.XMLTestRunner'
TEST_OUTPUT_FILE_NAME = os.path.join(BUILD_DIR, 'test-results.xml')
TEST_OUTPUT_DESCRIPTIONS = True
TEST_OUTPUT_VERBOSE = True

AMQP_HOST = os.getenv("AMQP_HOST", "localhost")

# The name of the AMQP queue that the engine2 pipeline expects input on
AMQP_PIPELINE_TARGET = "os2ds_scan_specs"

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'os2datascanner.projects.admin.adminapp.apps.AdminappConfig',
    'recurrence',
    'django_xmlrpc',
)

try:
    # if installed, add django_extensions for its many useful commands
    import django_extensions  # noqa

    INSTALLED_APPS += (
        'django_extensions',
    )
except ImportError:
    pass

XMLRPC_METHODS = (
    ('os2datascanner.projects.admin.adminapp.rpc.scan_urls', 'scan_urls'),
    ('os2datascanner.projects.admin.adminapp.rpc.scan_documents', 'scan_documents'),
    ('os2datascanner.projects.admin.adminapp.rpc.get_status', 'get_status'),
    ('os2datascanner.projects.admin.adminapp.rpc.get_report', 'get_report'),
)
MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_structlog.middlewares.RequestMiddleware',
)

ROOT_URLCONF = 'os2datascanner.projects.admin.urls'

WSGI_APPLICATION = 'os2datascanner.projects.admin.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'os2datascanner',
        'USER': 'os2datascanner',
        'PASSWORD': 'os2datascanner',
        'HOST': os.getenv('POSTGRES_HOST', '127.0.0.1'),
    }
}

DATABASE_POOL_ARGS = {
    'max_overflow': 10,
    'pool_size': 5,
    'recycle': 300
}

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'da-dk'

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'adminapp', 'locale'),
)

LANGUAGES = (
    ('da', _('Danish')),
    ('en', _('English')),
)

TIME_ZONE = 'Europe/Copenhagen'

USE_I18N = True

USE_L10N = True

USE_TZ = True

USE_THOUSAND_SEPARATOR = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
AUTH_PROFILE_MODULE = 'os2datascanner.projects.admin.adminapp.UserProfile'
ICON_SPRITE_URL = '/static/src/svg/symbol-defs.svg'

LOGIN_REDIRECT_URL = '/'

# Email settings

DEFAULT_FROM_EMAIL = 'os2webscanner@magenta.dk'
ADMIN_EMAIL = 'os2webscanner@magenta.dk'
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

# Directory to mount network drives
NETWORKDRIVE_TMP_PREFIX = '/tmp/mnt/os2webscanner/'

# Always store temp files on disk
FILE_UPLOAD_MAX_MEMORY_SIZE = 0

# Hostname to use for logging to Graylog; its absence supresses such
# logging
GRAYLOG_HOST = os.getenv('DJANGO_GRAYLOG_HOST')

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        # structlog.processors.ExceptionPrettyPrinter(),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    context_class=structlog.threadlocal.wrap_dict(dict),
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)


# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        "gelf": {
            "()": "os2datascanner.utils.gelf.GELFFormatter",
        },
        "json": {
            "()": "structlog.stdlib.ProcessorFormatter",
            "processor": structlog.processors.JSONRenderer(),
        },
        "console": {
            "()": "structlog.stdlib.ProcessorFormatter",
            "processor": structlog.dev.ConsoleRenderer(),
        },
        "key_value": {
            "()": "structlog.stdlib.ProcessorFormatter",
            "processor": structlog.processors.KeyValueRenderer(key_order=[
                'timestamp',
                'level',
                'event',
                'logger',
            ]),
        },
        'verbose': {
            'format': (
                '%(levelname)s %(asctime)s %(module)s %(process)d '
                '%(thread)d %(message)s'
            ),
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
        "requires_graylog_host": {
            "()": "django.utils.log.CallbackFilter",
            "callback": lambda record: bool(GRAYLOG_HOST),
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            'filters': ['require_debug_true'],
            "formatter": "console",
        },
        "debug_log": {
            "level": "DEBUG",
            "class": "logging.handlers.WatchedFileHandler",
            "filename": VAR_DIR + '/debug.log',
            'filters': ['require_debug_true'],
            "formatter": "key_value",
        },
        "graylog": {
            "level": "DEBUG",
            "class": "os2datascanner.utils.gelf.GraylogDatagramHandler",
            "host": GRAYLOG_HOST,
            "filters": ["requires_graylog_host"],
            "formatter": "gelf",
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django_structlog': {
            'handlers': ['console', 'debug_log', 'graylog'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': True,
        },
        'os2datascanner': {
            'handlers': ['console', 'debug_log', 'graylog'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': True,
        },
    }
}

local_settings_file = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'local_settings.py'
)
if os.path.exists(local_settings_file):
    from .local_settings import *  # noqa
