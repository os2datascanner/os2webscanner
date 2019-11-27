import os
import json
import errno
from random import randrange
from tempfile import NamedTemporaryFile
from contextlib import contextmanager
from prometheus_client import start_http_server


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
    os.makedirs(advertisement_directory, exist_ok=True)
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
