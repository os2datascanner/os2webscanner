import os.path
from abc import abstractmethod
from mimetypes import guess_type

from ...utilities.json import JSONSerialisable
from ...utilities.equality import TypePropertyEquality
from .errors import UnknownSchemeError, DeserialisationError
from .source import Source


class Handle(TypePropertyEquality, JSONSerialisable):
    """A Handle is a reference to a leaf node in a hierarchy maintained by a
    Source. Handles can be followed to give a Resource, a concrete object.

    Although all Handle subclasses expose the same two-argument constructor,
    which takes a Source and a string representation of a path, each type of
    Source defines what its Handles and their paths mean; the only general way
    to get a meaningful Handle is the Source.handles() method (or to make a
    copy of an existing one).

    Handles are serialisable and persistent, and two different Handles with the
    same type and properties compare equal."""

    @property
    @abstractmethod
    def type_label(self) -> str:
        """A label that will be used to identify JSON forms of this Handle."""

    @property
    @abstractmethod
    def resource_type(self) -> type:
        """The subclass of Resource produced when this Handle is followed."""

    def __init__(self, source, relpath):
        self._source = source
        self._relpath = relpath

    @property
    def source(self):
        """Returns this Handle's Source."""
        return self._source

    @property
    def relative_path(self):
        """Returns this Handle's path."""
        return self._relpath

    @property
    def name(self):
        """Returns the base name -- everything after the last '/' -- of this
        Handle's path, or "file" if the result would otherwise be empty."""
        return os.path.basename(self._relpath) or 'file'

    def guess_type(self):
        """Guesses the type of this Handle's target based on its name. (For a
        potentially better, but more expensive, guess, follow this Handle to
        get a Resource and call its compute_type() method instead.)"""
        mime, _ = guess_type(self.name)
        return mime or "application/octet-stream"

    @property
    @abstractmethod
    def presentation(self):
        """Returns a (perhaps localised) human-readable string representing
        this Handle, for use in user interfaces."""

    @property
    def presentation_url(self):
        """Returns a URL that points to a user-meaningful webpage that
        corresponds to this Handle, if there is one.

        The returned URL is not necessarily the result of appending this
        Handle's path to the URL representation of its Source. (For example,
        this function might, for a Handle identifying an email, return a URL
        that points at that email in an appropriate webmail system.)"""
        return None

    @abstractmethod
    def censor(self):
        """Returns a Handle identical to this one but whose Source does not
        carry sensitive information like passwords or API keys. See the
        documentation of Source.censor for more information.

        As the Handle returned by this method is not useful for anything other
        than identifying an object, this method should normally only be used
        when transmitting a Handle to a less trusted context."""

    def __str__(self):
        return self.presentation

    def follow(self, sm):
        """Follows this Handle using the state in the StateManager @sm,
        returning a concrete Resource."""
        return self.resource_type(self, sm)

    BASE_PROPERTIES = ('_source', '_relpath',)
    """The properties defined by Handle. (If a subclass defines other
    properties, but wants those properties to be ignored when comparing
    objects, it should set the 'eq_properties' class attribute to this
    value.)"""

    _json_handlers = {}

    def to_json_object(self):
        """Returns an object suitable for JSON serialisation that represents
        this Handle."""
        return {
            "type": self.type_label,
            "source": self.source.to_json_object(),
            "path": self.relative_path
        }

    @staticmethod
    def stock_json_handler(type_label):
        """Decorator: registers the decorated class as a simple handler
        for the type label given as an argument. The class's two-argument
        constructor will be called with a Source and a path."""
        def _stock_json_handler(cls):
            @Handle.json_handler(type_label)
            def _invoke_constructor(obj):
                return cls(
                        Source.from_json_object(obj["source"]),
                        obj["path"])
            return cls
        return _stock_json_handler
