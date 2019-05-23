import functools
import os
import pathlib
import pkgutil
import sys
import typing
import urllib.parse
import urllib.request

import django

import os.path
import json
import errno
from contextlib import contextmanager
from random import randrange
from prometheus_client import start_http_server

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


@contextmanager
def prometheus_session(name, **kwargs):
    while True:
        # Find a free port to serve Prometheus metrics over...
        try:
            port = randrange(45000, 55000)
            start_http_server(port)
            break
        except OSError as ex:
            if ex.errno == errno.EADDRINUSE:
                continue
            else:
                raise

    # ... advertise this port, and this service, to Prometheus...
    print(__file__)
    advertisement_path = os.path.dirname(__file__) + "/../../../prometheus/{0}.json".format(name)
    with open(advertisement_path, "w") as fp:
        json.dump([
            {
                "targets": ["localhost:{0}".format(port)],
                "labels": kwargs
            }
        ], fp)
        fp.flush()
        os.fsync(fp.fileno())

    # ... yield...
    yield

    # ... and, finally, delete the service advertisement
    os.unlink(advertisement_path)
