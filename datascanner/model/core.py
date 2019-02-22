import magic
from pathlib import Path
from mimetypes import guess_type
from subprocess import run, PIPE, DEVNULL

class Error(Exception):
    pass

class _TypPropEq:
    """\
Secret mixin! Classes inheriting from _TypPropEq compare equal if their types
and properties -- as determined by __getstate__() or __dict__ -- compare equal.
"""
    @staticmethod
    def __get_comparator(key):
        if hasattr(key, '__getstate__'):
            return key.__getstate__()
        else:
            return key.__dict__

    def __eq__(self, key):
        return type(self) == type(key) and \
                _TypPropEq.__get_comparator(self) == \
                _TypPropEq.__get_comparator(key)

    def __hash__(self):
        h = 42 + hash(type(self))
        for k, v in _TypPropEq.__get_comparator(self).items():
            h += hash(k) + (hash(v) * 3)
        return h

class Source(_TypPropEq):
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
    def _open(self, sm):
        """\
Opens this Source in the given SourceManager. Returns a cookie of some kind
that can be used to interact with the opened state, and which SourceManager
will later pass to _close.
"""
        raise NotImplemented("Source._open")

    def _close(self, cookie):
        """\
Closes a cookie previously returned by _open."""
        raise NotImplemented("Source._close")

    def handles(self, sm):
        """\
Yields Handles corresponding to every leaf node in this hierarchy. These
Handles are generated in an undefined order."""
        raise NotImplemented("Source.handles")

    def to_url(self):
        """\
Returns a representation of this Source as a URL. The resulting URL can be
passed to the Source.from_url function to produce a new Source that compares
equal to this one."""
        raise NotImplemented("Source.to_url")

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

SourceManagers are not serialisable. (They're /supposed/ to be not
serialisable! They track all of the state that would otherwise make Sources and
Handles unserialisable!)
"""
    def __init__(self, parent=None):
        """\
Initialises this SourceManager.

If @parent is not None, then it *must* be a SourceManager operating as a
context manager in a containing scope."""
        self._order = []
        self._opened = {}
        self._parent = parent

    def open(self, source, try_open=True):
        """\
Returns the cookie returned by opening the given Source. If @try_open is True,
the Source will be opened in this SourceManager if necessary."""
        if not source in self._opened:
            cookie = None
            if self._parent:
                cookie = self._parent.open(source, try_open=False)
            if not cookie and try_open:
                cookie = source._open(self)
                self._order.append(source)
                self._opened[source] = cookie
            return cookie
        else:
            return self._opened[source]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, backtrace):
        """\
Closes all of the cookies returned by Sources that were opened in this
SourceManager."""
        try:
            for k in reversed(self._order):
                k._close(self._opened[k])
        finally:
            self._order = []
            self._opened = {}

class Handle(_TypPropEq):
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

    def follow(self, sm):
        """\
Follows this Handle using the state in the StateManager @sm, returning a
concrete Resource."""
        raise NotImplementedError("Handle.follow")

class Resource:
    """\
A Resource is a concrete embodiment of an object: it's the thing a Handle
points to. Although it has some file-like properties, it's not necessarily an
object in the local filesystem.

The Resource.make_path() function returns a context manager that ensures that
the object the Resource refers to is available on the local filesystem at the
returned path for the life of the context. Resource.make_stream() does the
same thing, but returns an open, read-only Python stream for the object instead
of a path.

Resources are short-lived -- they should only be used when you actually need to
get to a file's contents. As such, they are not serialisable."""
    def __init__(self, handle, sm):
        self._handle = handle
        self._sm = sm

    def get_handle(self):
        return self._handle
    def _open_source(self):
        return self._sm.open(self.get_handle().get_source())

    def get_hash(self):
        """\
Returns a hash for this Resource. (No particular hash algorithm is defined for
this, but all Resources generated by a Source should use the same one.)
"""
        raise NotImplementedError("Resource.get_hash")

    def get_last_modified(self):
        raise NotImplementedError("Resource.get_last_modified")

    def make_path(self):
        raise NotImplementedError("Resource.make_path")

    def make_stream(self):
        raise NotImplementedError("Resource.make_stream")

    def compute_type(self):
        """\
Guesses the type of this file, possibly examining its content in the process.
By default, this is computed by giving libmagic the first 512 bytes of the
file."""
        with self.make_stream() as s:
            return magic.from_buffer(s.read(512), True)
