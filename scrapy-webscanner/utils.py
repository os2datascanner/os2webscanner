import os
import pathlib
import sys
import typing
import urllib.parse
import urllib.request

import django


def load_webscanner_settings():
    """Load webscanner settings into environment"""
    base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sys.path.append(base_dir + "/webscanner_site")
    os.environ["DJANGO_SETTINGS_MODULE"] = "webscanner.settings"


def run_django_setup():
    """Load django setup and include django app"""
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
        return urllib.url2pathname(urllib.urlparse(path).path)
    else:
        return path
