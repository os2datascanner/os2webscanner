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

    SourceManagers can be nested to an arbitrary depth, provided that their
    contexts are also nested; child SourceManagers will not try to open Sources
    that their antecedents have already opened, and the nesting ensures that
    their own state will be cleaned up before that of their antecedents.

    As SourceManagers track (potentially process-specific) state, they are not
    usefully serialisable. See, however, the SourceManager.share method and
    the ShareableCookie class below."""
    def __init__(self, parent=None):
        """Initialises this SourceManager.

        If @parent is not None, then it *must* be a SourceManager operating as
        a context manager in a containing scope."""
        self._order = []
        self._opened = {}
        self._parent = parent
        self._ro = False

    def share(self):
        """Returns a SourceManager that contains only the ShareableCookies from
        this SourceManager. This SourceManager will be read-only, and can only
        be used as a parent for a writable SourceManager: attempting to open
        things in it, or to enter its context, will raise a TypeError."""
        if self._ro:
            return self
        r = SourceManager()
        r._parent = self._parent.share() if self._parent else None
        r._ro = True
        for v in self._order:
            (generator, cookie) = self._opened[v]
            if isinstance(cookie, ShareableCookie):
                r._order.append(v)
                r._opened[v] = (None, cookie)
        return r

    def open(self, source, try_open=True):
        """Returns the cookie returned by opening the given Source. If
        @try_open is True, the Source will be opened in this SourceManager if
        necessary."""
        if self._ro and try_open:
            raise TypeError(
                    "BUG: open(try_open=True) called on" +
                    " a read-only SourceManager!")
        rv = None
        if not source in self._opened:
            cookie = None
            if self._parent:
                cookie = self._parent.open(source, try_open=False)
            if not cookie and try_open:
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
        if self._ro:
            raise TypeError(
                    "BUG: __enter__ called on a read-only SourceManager!")
        return self

    def __exit__(self, exc_type, exc_value, backtrace):
        """Closes all of the cookies returned by Sources that were opened in
        this SourceManager."""
        try:
            for k in reversed(self._order):
                generator, _ = self._opened[k]
                if not generator and not self._ro:
                    raise TypeError(
                            "BUG: __exit__ on a normal SourceManager"
                            + " encountered a None generator!")
                else:
                    generator.close()
        finally:
            self._order = []
            self._opened = {}
