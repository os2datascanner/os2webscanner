from abc import ABC, abstractmethod

from .errors import UnknownSchemeError, DeserialisationError
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

    type_label = None
    """A label that will be used to identify JSON forms of this Source."""

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

        Note that this method can yield Handles that correspond to
        identifiable *but non-existent* leaf nodes. These might correspond to,
        for example, a broken link on a web page, or to an object that was
        yielded by this method but was deleted before it could be examined.
        These Handles can be detected by catching the ResourceUnavailableError
        exception.

        It is not necessarily the case that the result of the get_source call
        on a Handle yielded by this method will be this Source."""

    __url_handlers = {}
    @staticmethod
    def url_handler(*schemes):
        """Decorator: registers the decorated function as the handler for the
        URL schemes given as arguments. This handler will be called by from_url
        when it finds one of these schemes.

        Subclasses should use this decorator to register their from_url factory
        methods."""
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
        """Decorator: registers the decorated function as the handler for the
        MIME types given as arguments. This handler will be called by
        from_handle when it finds one of these MIME types.

        Subclasses should use this decorator to register their from_handle
        factory methods, if they implement such a method."""
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
        Source.from_handle method), then returns that Handle; otherwise,
        returns None."""
        return None

    @abstractmethod
    def to_json_object(self):
        """Returns an object suitable for JSON serialisation that represents
        this Source."""
        return {
            "type": self.type_label
        }

    __json_handlers = {}
    @staticmethod
    def json_handler(type_label):
        """Decorator: registers the decorated function as the handler for the
        type label given as an argument. This handler will be called by
        from_json_object when it finds this type label.

        Subclasses should use this decorator to register their from_json_object
        factory methods."""
        def _json_handler(func):
            if type_label in Source.__json_handlers:
                raise ValueError(
                        "BUG: can't register two handlers" +
                        " for the same JSON type label!", type_label)
            Source.__json_handlers[type_label] = func
            return func
        return _json_handler

    @staticmethod
    def from_json_object(obj):
        """Converts a JSON representation of a Source, as returned by the
        Source.to_json_object method, back into a Source."""
        try:
            tl = obj["type"]
            if not tl in Source.__json_handlers:
                raise UnknownSchemeError(tl)
            return Source.__json_handlers[tl](obj)
        except KeyError as k:
            tl = obj.get("type", None)
            raise DeserialisationError(tl, k.args[0])
