import functools
import os
import pathlib
import pkgutil
import typing
import urllib.parse
import urllib.request

import django


def run_django_setup():
    """Load django setup and include django app"""
    os.environ["DJANGO_SETTINGS_MODULE"] = "os2datascanner.projects.admin.settings"
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


@functools.lru_cache()
def get_data(file_name: str, uppercase=True) -> typing.FrozenSet[str]:
    '''Obtain the given data file from the package data'''

    data = pkgutil.get_data(__name__, os.path.join('data', file_name))

    assert data is not None

    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        text = data.decode('latin-1')

    if uppercase:
        text = text.upper()

    return frozenset(
        line.split('\t', 1)[0]
        for line in text.splitlines()
        if line
    )
