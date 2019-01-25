from urllib.parse import quote, unquote, urlsplit, urlunsplit
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
same type and properties compare equal.
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
        scheme, netloc, path, _, _ = urlsplit(url)
        if not scheme in Source.__url_handlers:
            raise UnknownSchemeError(scheme)
        return Source.__url_handlers[scheme](
                scheme, netloc, unquote(path) if path else None)

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

SourceManagers are not serialisable. (They're /supposed/ to be not
serialisable! They track all of the state that would otherwise make Sources and
Handles unserialisable!)
"""
    def __init__(self):
        self._order = []
        self._opened = {}

    def is_open(self, source):
        """\
Indicates whether or not the given Source has been opened in this
SourceManager."""
        return source in self._opened

    def open(self, source):
        """\
Returns the cookie returned by opening the given Source (which will be opened
in this SourceManager, if it wasn't already)."""
        if not self.is_open(source):
            o = source._open(self)
            self._order.append(source)
            self._opened[source] = o
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

There is no defined way to get a Handle other than for a Source to generate one
(or to make a copy of an existing one). Each type of Source defines what its
Handles and their paths mean.

Handles are serialisable and persistent, and two different Handles with the
same type and properties compare equal.
"""
    def __init__(self, source, relpath):
        self._source = source
        self._relpath = relpath

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

When used as a context manager, a Resource will ensure that the object it
refers to is available on the local filesystem at the returned path for the
life of the context.

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

    def compute_type(self):
        """\
Guesses the type of this file, possibly examining its content in the process.
By default, this is computed using file(1)."""
        with self as fspath:
            return run(["file", "--brief", "--mime-type", fspath],
                    universal_newlines=True,
                    stdout=PIPE,
                    stderr=DEVNULL).stdout.strip()
