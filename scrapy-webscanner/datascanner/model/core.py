from abc import ABC, abstractmethod
import magic
from pathlib import Path
from mimetypes import guess_type
from subprocess import run, PIPE, DEVNULL

from .utilities import _TypPropEq

class Error(Exception):
    pass

class Source(ABC, _TypPropEq):
    """\
A Source represents the root of a hierarchy to be explored. It constructs
Handles, which represent the position of an object in the hierarchy.

Sources hold all the information (if any) needed to open a connection to their
hierarchy, but they aren't responsible for holding actual connection state --
that gets stashed in a SourceManager instead.

Sources are serialisable and persistent, and two different Sources with the
same type and properties compare equal. (One useful consequence of this is that
SourceManager will collapse several equal Sources together, only opening one of
them.)
"""

    @abstractmethod
    def _open(self, sm):
        """\
Opens this Source in the given SourceManager. Returns a cookie of some kind
that can be used to interact with the opened state, and which SourceManager
will later pass to _close."""

    @abstractmethod
    def _close(self, cookie):
        """\
Closes a cookie previously returned by _open."""

    @abstractmethod
    def handles(self, sm):
        """\
Yields Handles corresponding to every leaf node in this hierarchy. These
Handles are generated in an undefined order."""

    __url_handlers = {}
    @staticmethod
    def _register_url_handler(scheme, handler):
        assert not scheme in Source.__url_handlers
        Source.__url_handlers[scheme] = handler

    @staticmethod
    def from_url(url):
        """\
Parses the given URL to produce a new Source."""
        try:
            scheme, _ = url.split(':', maxsplit=1)
            if not scheme in Source.__url_handlers:
                raise UnknownSchemeError(scheme)
            return Source.__url_handlers[scheme](url)
        except ValueError:
            raise UnknownSchemeError()

    __mime_handlers = {}
    @staticmethod
    def _register_mime_handler(mime, constructor):
        assert not mime in Source.__mime_handlers
        Source.__mime_handlers[mime] = constructor

    @staticmethod
    def from_handle(handle, sm=None):
        """\
Tries to create a Source from a Handle.

This will only work if the target of the Handle in question can meaningfully be
interpreted as the root of a hierarchy of its own -- for example, if it's an
archive."""
        if not sm:
            mime = handle.guess_type()
        else:
            mime = handle.follow(sm).compute_type()
        if mime in Source.__mime_handlers:
            return Source.__mime_handlers[mime](handle)
        else:
            return None

class UnknownSchemeError(Error):
    pass

class SourceManager:
    """\
A SourceManager is responsible for tracking all of the state associated with
one or more Sources. Operations on Sources and Handles that require persistent
state use a SourceManager to keep track of that state.

When used as a context manager, a SourceManager will automatically clean up all
of the state that it's been tracking at context exit time. This might mean, for
example, automatically disconnecting from remote resources, unmounting drives,
or closing file handles.

SourceManagers can be nested to an arbitrary depth, provided that their
contexts are also nested; child SourceManagers will not try to open Sources
that their antecedents have already opened, and the nesting ensures that their
own state will be cleaned up before that of their antecedents.

As SourceManagers track (potentially process-specific) state, they are not
usefully serialisable. See, however, the SourceManager.share function and the
ShareableCookie class below."""
    def __init__(self, parent=None):
        """\
Initialises this SourceManager.

If @parent is not None, then it *must* be a SourceManager operating as a
context manager in a containing scope."""
        self._order = []
        self._opened = {}
        self._parent = parent
        self._ro = False

    def share(self):
        """\
Returns a copy of this SourceManager that contains only ShareableCookies. (The
resulting SourceManager can only safely be used as a parent.)"""
        r = SourceManager()
        r._ro = True
        for v in self._order:
            cookie = self._opened[v]
            if isinstance(cookie, ShareableCookie):
                r._order.append(cookie)
                r._opened[v] = cookie
        return r

    def open(self, source, try_open=True):
        """\
Returns the cookie returned by opening the given Source. If @try_open is True,
the Source will be opened in this SourceManager if necessary."""
        assert not (self._ro and try_open), """\
BUG: open(try_open=True) called on a read-only SourceManager!"""
        rv = None
        if not source in self._opened:
            cookie = None
            if self._parent:
                cookie = self._parent.open(source, try_open=False)
            if not cookie and try_open:
                cookie = source._open(self)
                self._order.append(source)
                self._opened[source] = cookie
            rv = cookie
        else:
            rv = self._opened[source]
        if isinstance(rv, ShareableCookie):
            return rv.get()
        else:
            return rv

    def __enter__(self):
        assert not self._ro, """\
BUG: __enter__ called on a read-only SourceManager!"""
        return self

    def __exit__(self, exc_type, exc_value, backtrace):
        """\
Closes all of the cookies returned by Sources that were opened in this
SourceManager."""
        try:
            for k in reversed(self._order):
                cookie = self._opened[k]
                if isinstance(cookie, ShareableCookie):
                    cookie = cookie.get()
                k._close(cookie)
        finally:
            self._order = []
            self._opened = {}

class ShareableCookie:
    """\
A Source's cookie represents the fact that it has been opened somehow.
Precisely what this means is not defined: it might represent a mount operation
on a remote drive, or a connection to a server, or even nothing at all.

The Source._open function can return a ShareableCookie to indicate that a
cookie can (for the duration of its SourceManager's context) meaningfully be
shared across processes, because the operations that it has performed are not
specific to a single process.

SourceManager will otherwise try to hide the existence of this class from the
outside world -- the value contained in this cookie, rather than the cookie
itself, will be returned from SourceManager.open and passed to
Source._close."""
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

EMPTY_COOKIE = ShareableCookie(None)
"""A contentless (and therefore trivially shareable) cookie."""

class Handle(ABC, _TypPropEq):
    """\
A Handle is a reference to a leaf node in a hierarchy maintained by a Source.
Handles can be followed to give a Resource, a concrete object.

Although all Handle subclasses expose the same two-argument constructor, which
takes a Source and a pathlib.Path, each type of Source defines what its Handles
and their paths mean; the only general way to get a meaningful Handle is the
Source.handles() function (or to make a copy of an existing one).

Handles are serialisable and persistent, and two different Handles with the
same type and properties compare equal.
"""
    def __init__(self, source, relpath):
        self._source = source
        if isinstance(relpath, Path):
            self._relpath = relpath
        else:
            self._relpath = Path(relpath)

    def get_source(self):
        return self._source

    def get_relative_path(self):
        return self._relpath

    def get_name(self):
        return self.get_relative_path().name

    def guess_type(self):
        """\
Guesses the type of this Handle's target based on its name. (For a potentially
better, but more expensive, guess, follow this Handle to get a Resource and
call its compute_type() method instead.)"""
        mime, _ = guess_type(self.get_name())
        return mime or "application/octet-stream"

    def __str__(self):
        return "{0}({1}, {2})".format(
                type(self).__name__, self._source, self._relpath)

    @abstractmethod
    def follow(self, sm):
        """\
Follows this Handle using the state in the StateManager @sm, returning a
concrete Resource."""

class Resource(ABC):
    """\
A Resource is a concrete embodiment of an object: it's the thing a Handle
points to. If you have a Resource, then you have some way of getting to the
data (and metadata) behind a Handle.

Most kinds of Resource behave, or can behave, like files; these are represented
by the FileResource subclass.

Resources are short-lived -- they should only be used when you actually need to
get to content. As such, they are not serialisable."""
    def __init__(self, handle, sm):
        self._handle = handle
        self._sm = sm

    def get_handle(self):
        return self._handle
    def _open_source(self):
        return self._sm.open(self.get_handle().get_source())

class FileResource(Resource):
    """\
A FileResource is a Resource that can, when necessary, be viewed as a file.

The Resource.make_path() function returns a context manager that ensures that
the object the Resource refers to is available on the local filesystem at the
returned path for the life of the context. Resource.make_stream() does the
same thing, but returns an open, read-only Python stream for the object instead
of a path."""
    def get_hash(self):
        """\
Returns a hash for this Resource. (No particular hash algorithm is defined for
this, but all Resources generated by a Source should use the same one.)"""

    @abstractmethod
    def get_last_modified(self):
        pass

    @abstractmethod
    def make_path(self):
        pass

    @abstractmethod
    def make_stream(self):
        pass

    def compute_type(self):
        """\
Guesses the type of this file, possibly examining its content in the process.
By default, this is computed by giving libmagic the first 512 bytes of the
file."""
        with self.make_stream() as s:
            return magic.from_buffer(s.read(512), True)
