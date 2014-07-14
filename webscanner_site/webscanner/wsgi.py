"""
WSGI config for webscanner project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webscanner.settings")

site_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..')
)
lib_path = 'python-env/lib/python2.7/site-packages'

install_dir = os.path.abspath(os.path.join(site_dir, '..'))
lib_dir = os.path.join(install_dir, lib_path)
webscanner_dir = os.path.join(install_dir, 'django-os2webscanner')

sys.path[0:0] = [site_dir, lib_dir, webscanner_dir]

try:
    import os2webscanner
except:
    raise RuntimeError("Path: " + str(sys.path))

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
