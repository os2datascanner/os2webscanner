from sys import stderr
from traceback import print_exc


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
        self._opened = {}
        self._opening = []

        self._paths = {}

    def _register_path(self, path):
        """Registers a path, a dependency list of Sources of the form [child,
        parent, grandparent, ...], with this SourceManager. Paths are used to
        decide which order to free resources in.

        Paths can be either complete (such as [file in Zip archive, Zip
        archive, network share]) or partial ([file in Zip archive, Zip
        archive]). Previously registered complete paths will be used to
        disambiguate partial paths.

        Paths are an internal implementation detail, and this function is
        intended for use only by SourceManager.open."""
        if len(path) > 1:
            # Convert the path [child, parent, grandparent, ..., ancestor K-1,
            # ancestor K] into a number of pairs of the form (ancestor K,
            # ancestor K-1), (ancestor K-1, ancestor K-2), ...,  (grandparent,
            # parent), (parent, child)
            for parent, child in zip(reversed(path), reversed(path[:-1])):
                children = self._paths.setdefault(parent, [])
                if child in children:
                    children.remove(child)
                children.append(child)

    def open(self, source):
        """Returns the cookie returned by opening the given Source."""
        self._opening.append(source)
        self._register_path(self._opening)
        try:
            rv = None
            if not source in self._opened:
                cookie = None
                if not cookie:
                    generator = source._generate_state(self)
                    cookie = next(generator)
                    self._opened[source] = (generator, cookie)
                rv = cookie
            else:
                _, rv = self._opened[source]
            if isinstance(rv, ShareableCookie):
                return rv.get()
            else:
                return rv
        finally:
            self._opening = self._opening[:-1]

    def close(self, source):
        """Closes a Source opened in this SourceManager, in the process closing
        all other open Sources that depend upon it."""
        if source in self._opened:
            # Leaf nodes will be in self._opened, but won't be in self._paths,
            # because nothing depends upon them
            if source in self._paths:
                for child in self._paths[source]:
                    self.close(child)
                del self._paths[source]
            generator, _ = self._opened[source]
            try:
                generator.close()  # not allowed to fail
            except Exception:
                stn = type(source).__name__
                print("*** BUG: {0}._generate_state raised an exception!"
                        " Continuing anyway...".format(stn), file=stderr)
                print_exc(file=stderr)
            del self._opened[source]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, backtrace):
        self.clear()

    def clear(self):
        """Closes all of the cookies returned by Sources that were opened in
        this SourceManager."""
        opened = list(self._opened.keys())
        for source in opened:
            self.close(source)
