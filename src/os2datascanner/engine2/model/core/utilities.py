class ShareableCookie:
    """A Source's cookie represents the fact that it has been opened somehow.
    Precisely what this means is not defined: it might represent a mount
    operation on a remote drive, or a connection to a server, or even nothing
    at all.

    Source._generate_state can yield a ShareableCookie to indicate that a
    cookie can (for the duration of its SourceManager's context) meaningfully
    be shared across processes, because the operations that it has performed
    are not specific to a single process.

    SourceManager will otherwise try to hide the existence of this class from
    the outside world -- the value contained in this cookie, rather than the
    cookie itself, will be returned from SourceManager.open and passed to
    Source._close."""
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

EMPTY_COOKIE = ShareableCookie(None)
"""A contentless (and therefore trivially shareable) cookie."""

class SourceManager:
    """A SourceManager is responsible for tracking all of the state associated
    with one or more Sources. Operations on Sources and Handles that require
    persistent state use a SourceManager to keep track of that state.

    When used as a context manager, a SourceManager will automatically clean up
    all of the state that it's been tracking at context exit time. This might
    mean, for example, automatically disconnecting from remote resources,
    unmounting drives, or closing file handles.

    As SourceManagers track (potentially process-specific) state, they are not
    usefully serialisable. See, however, the SourceManager.share method and
    the ShareableCookie class below."""
    def __init__(self):
        """Initialises this SourceManager."""
        self._order = []
        self._opened = {}
        self._dependencies = {}

    def open(self, source):
        """Returns the cookie returned by opening the given Source."""
        rv = None
        if not source in self._opened:
            cookie = None
            if not cookie:
                generator = source._generate_state(self)
                cookie = next(generator)
                self._order.append(source)
                self._opened[source] = (generator, cookie)
            rv = cookie
        else:
            _, rv = self._opened[source]
        if isinstance(rv, ShareableCookie):
            return rv.get()
        else:
            return rv

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, backtrace):
        self.clear()

    def clear(self):
        """Closes all of the cookies returned by Sources that were opened in
        this SourceManager."""
        try:
            for k in reversed(self._order):
                generator, _ = self._opened[k]
                generator.close()
        finally:
            self._order = []
            self._opened = {}
