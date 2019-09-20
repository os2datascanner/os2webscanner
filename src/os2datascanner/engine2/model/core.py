from abc import ABC, abstractmethod
import magic
import os.path
from mimetypes import guess_type

from .utilities import _TypPropEq

class Source(ABC, _TypPropEq):
    """A Source represents the root of a hierarchy to be explored. It
    constructs Handles, which represent the position of an object in the
    hierarchy.

    Sources hold all the information (if any) needed to open a connection to
    their hierarchy, but they aren't responsible for holding actual connection
    state -- that gets stashed in a SourceManager instead.

    Sources are serialisable and persistent, and two different Source objects
    with the same type and properties compare equal. (One useful consequence of
    this is that SourceManager will collapse several equal Sources together,
    only opening one of them.)"""

    @abstractmethod
    def _generate_state(self, sm):
        """Returns a state management generator. This generator will only be
        executed once: this will yield a magic cookie representing any state
        that this Source might require. The generator will be closed when
        this state is no longer needed.

        The relevant instance properties when considering Source equality are
        normally only those properties used by this method. (The default
        implementation is conservative, however, and compares all
        properties.)"""

    @abstractmethod
    def handles(self, sm):
        """Yields Handles corresponding to every identifiable leaf node in this
        Source's hierarchy. These Handles are generated in an undefined order.

        Note that this function can yield Handles that correspond to
        identifiable *but non-existent* leaf nodes. These might correspond to,
        for example, a broken link on a web page, or to an object that was
        yielded by this function but was deleted before it could be examined.
        These Handles can be detected by catching the ResourceUnavailableError
        exception.

        It is not necessarily the case that the result of the get_source call
        on a Handle yielded by this function will be this Source."""

    __url_handlers = {}
    @staticmethod
    def url_handler(*schemes):
        def _url_handler(func):
            for scheme in schemes:
                if scheme in Source.__url_handlers:
                    raise ValueError(
                            "BUG: can't register two handlers" +
                            " for the same URL scheme!", scheme)
                Source.__url_handlers[scheme] = func
            return func
        return _url_handler

    @staticmethod
    def from_url(url):
        """Parses the given URL to produce a new Source."""
        try:
            scheme, _ = url.split(':', maxsplit=1)
            if not scheme in Source.__url_handlers:
                raise UnknownSchemeError(scheme)
            return Source.__url_handlers[scheme](url)
        except ValueError:
            raise UnknownSchemeError()

    # There is no general requirement that subclasses implement a to_url
    # method (what's the URL of a file in a deeply-nested archive?), but many
    # of them do. If a Source provides a to_url method, it is a requirement
    # that Source.from_url(Source.to_url(src)) == src.

    __mime_handlers = {}
    @staticmethod
    def mime_handler(*mimes):
        def _mime_handler(func):
            for mime in mimes:
                if mime in Source.__mime_handlers:
                    raise ValueError(
                            "BUG: can't register two handlers" +
                            " for the same MIME type!", mime)
                Source.__mime_handlers[mime] = func
            return func
        return _mime_handler

    @staticmethod
    def from_handle(handle, sm=None):
        """Tries to create a Source from a Handle.

        This will only work if the target of the Handle in question can
        meaningfully be interpreted as the root of a hierarchy of its own --
        for example, if it's an archive."""
        if not sm:
            mime = handle.guess_type()
        else:
            mime = handle.follow(sm).compute_type()
        if mime in Source.__mime_handlers:
            return Source.__mime_handlers[mime](handle)
        else:
            return None

    def to_handle(self):
        """If this Source was created based on a Handle (typically by the
        Source.from_handle function), then returns that Handle; otherwise,
        returns None."""
        return None

class UnknownSchemeError(LookupError):
    """When Source.from_url does not know how to handle a given URL, either
    because no Source subclass is registered as a handler for its scheme or
    because the URL is not valid, an UnknownSchemeError will be raised.
    Its only associated value is a string identifying the scheme, if one was
    present in the URL."""

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
    usefully serialisable. See, however, the SourceManager.share function and
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
            cookie = self._opened[v]
            if isinstance(cookie, ShareableCookie):
                r._order.append(cookie)
                r._opened[v] = cookie
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
                generator.close()
        finally:
            self._order = []
            self._opened = {}

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

class Handle(ABC, _TypPropEq):
    """A Handle is a reference to a leaf node in a hierarchy maintained by a
    Source. Handles can be followed to give a Resource, a concrete object.

    Although all Handle subclasses expose the same two-argument constructor,
    which takes a Source and a string representation of a path, each type of
    Source defines what its Handles and their paths mean; the only general way
    to get a meaningful Handle is the Source.handles() function (or to make a
    copy of an existing one).

    Handles are serialisable and persistent, and two different Handles with the
    same type and properties compare equal."""
    def __init__(self, source, relpath):
        self._source = source
        self._relpath = relpath

    def get_source(self):
        """Returns this Handle's Source."""
        return self._source

    def get_relative_path(self):
        """Returns this Handle's path."""
        return self._relpath

    def get_name(self):
        """Returns the base name -- everything after the last '/' -- of this
        Handle's path, or "file" if the result would otherwise be empty."""
        return os.path.basename(self._relpath) or 'file'

    def guess_type(self):
        """Guesses the type of this Handle's target based on its name. (For a
        potentially better, but more expensive, guess, follow this Handle to
        get a Resource and call its compute_type() method instead.)"""
        mime, _ = guess_type(self.get_name())
        return mime or "application/octet-stream"

    def __str__(self):
        return "{0}({1}, {2})".format(
                type(self).__name__, self._source, self._relpath)

    @abstractmethod
    def follow(self, sm):
        """Follows this Handle using the state in the StateManager @sm,
        returning a concrete Resource."""

    BASE_PROPERTIES = ('_source', '_relpath',)
    """The properties defined by Handle. (If a subclass defines other
    properties, but wants those properties to be ignored when comparing
    objects, it should set the 'eq_properties' class attribute to this
    value.)"""

class Resource(ABC):
    """A Resource is a concrete embodiment of an object: it's the thing a
    Handle points to. If you have a Resource, then you have some way of getting
    to the data (and metadata) behind a Handle.

    Most kinds of Resource behave, or can behave, like files; these are
    represented by the FileResource subclass.

    Resources are short-lived -- they should only be used when you actually
    need to get to content. As such, they are not serialisable."""
    def __init__(self, handle, sm):
        self._handle = handle
        self._sm = sm

    def get_handle(self):
        """Returns this Resource's Handle."""
        return self._handle

    def _get_cookie(self):
        """Returns the magic cookie produced when the Source behind this
        Resource's Handle is opened in the associated StateManager. (Note that
        each Source will only be opened once by a given StateManager.)"""
        return self._sm.open(self.get_handle().get_source())

class ResourceUnavailableError(Exception):
    """When a function that tries to access a Resource's data or metadata
    fails, a ResourceUnavailableError will be raised. The first associated
    value will be the Handle backing the Resource in question; subsequent
    values, if present, give specific details of the failure."""

    def __str__(self):
        hand, args = self.args[0], self.args[1:]
        if args:
            return "ResourceUnavailableError({0}, {1})".format(
                    hand, ", ".join([str(arg) for arg in args]))
        else:
            return "ResourceUnavailableError({0})".format(hand)

class FileResource(Resource):
    """A FileResource is a Resource that can, when necessary, be viewed as a
    file."""
    def get_hash(self):
        """Returns a hash for this FileResource's content. (No particular hash
        algorithm is defined for this, but all FileResources generated by a
        Source should use the same one.)"""

    @abstractmethod
    def get_size(self):
        """Returns the size of this FileResource's content, in bytes."""

    @abstractmethod
    def get_last_modified(self):
        """Returns the last modification date of this FileResource as a Python
        datetime.datetime."""

    @abstractmethod
    def make_path(self):
        """Returns a context manager that, when entered, returns a path through
        which the content of this FileResource can be accessed until the
        context is exited. (Do not attempt to write to this path -- the result
        is undefined.)"""

    @abstractmethod
    def make_stream(self):
        """Returns a context manager that, when entered, returns a read-only
        Python stream through which the content of this FileResource can be
        accessed until the context is exited."""

    def compute_type(self):
        """Guesses the type of this file, possibly examining its content in the
        process. By default, this is computed by giving libmagic the first 512
        bytes of the file."""
        with self.make_stream() as s:
            return magic.from_buffer(s.read(512), True)
