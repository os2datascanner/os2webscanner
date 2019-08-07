import functools
import os
import pathlib
import pkgutil
import typing
import urllib.parse
import urllib.request

import django

import os.path
import json
import errno

from random import randrange
from tempfile import NamedTemporaryFile
from contextlib import contextmanager
from prometheus_client import start_http_server

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


@contextmanager
def prometheus_session(name, advertisement_directory, **kwargs):
    # Find a free port to serve Prometheus metrics over...
    while True:
        try:
            # start_http_server tells us nothing about the HTTP server thread
            # that it created, so we can't just pass a port of 0 -- we need to
            # know which port it's using in order to be able to create the
            # advertisement file (groan)
            port = randrange(5000, 65000)
            start_http_server(port)
            break
        except OSError as ex:
            if ex.errno == errno.EADDRINUSE:
                continue
            else:
                raise

    # ... advertise this port, and this service, to Prometheus...
    with NamedTemporaryFile(mode="wt", dir=advertisement_directory,
            delete=False) as fp:
        tmpfile = fp.name
        # (... making sure that other users can read the advertisement...)
        os.chmod(tmpfile, 0o644)

        json.dump([
            {
                "targets": ["localhost:{0}".format(port)],
                "labels": kwargs
            }
        ], fp)
    advertisement_path = advertisement_directory + ("/{0}.json".format(name))
    os.rename(tmpfile, advertisement_path)

    # ... and yield to execute whatever's in the with block
    yield

    # Now that we're back and the context has finished, delete the service
    # advertisement
    os.unlink(advertisement_path)
