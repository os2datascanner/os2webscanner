"""
WSGI config for webscanner project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import os
import sys
import pathlib

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "os2datascanner.projects.admin.settings")

PROJECT_DIR = str(pathlib.Path(__file__).resolve().parent.parent.parent.parent.parent.absolute())

lib_path = 'python-env/lib/python3.6/site-packages'
lib_path1 = 'python-env/lib/python3.5/site-packages'

lib_dir = os.path.join(PROJECT_DIR, lib_path)
lib_dir1 = os.path.join(PROJECT_DIR, lib_path1)
src_dir = os.path.join(PROJECT_DIR, 'src')

sys.path[0:0] = [PROJECT_DIR, lib_dir, lib_dir1, src_dir]

try:
    import os2datascanner.projects.admin.adminapp
except Exception:
    raise RuntimeError("Path: " + str(sys.path))

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
