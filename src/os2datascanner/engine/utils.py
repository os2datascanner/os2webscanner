import os
import pathlib
import sys
import typing
import urllib.parse
import urllib.request

import django


def run_django_setup():
    """Load django setup and include django app"""
    os.environ["DJANGO_SETTINGS_MODULE"] = "os2datascanner.sites.admin.settings"
    django.setup()


def as_file_uri(path: typing.Union[str, pathlib.Path]) -> str:
    # TODO: consolidate with `django-os2webscanner/os2webscanner/utils.py`
    if isinstance(path, str) and path.startswith('file://'):
        return path
    elif not isinstance(path, pathlib.Path):
        path = pathlib.Path(path)

    return path.as_uri()


def as_path(path: str) -> str:
    if path.startswith('file://'):
        path = urllib.request.url2pathname(urllib.parse.urlparse(path).path)

    return pathlib.Path(path)
