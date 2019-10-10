import os.path
from abc import ABC, abstractmethod
from mimetypes import guess_type

from .errors import UnknownSchemeError, DeserialisationError
from .source import Source
from .utilities import _TypPropEq

class Handle(ABC, _TypPropEq):
    """A Handle is a reference to a leaf node in a hierarchy maintained by a
    Source. Handles can be followed to give a Resource, a concrete object.

    Although all Handle subclasses expose the same two-argument constructor,
    which takes a Source and a string representation of a path, each type of
    Source defines what its Handles and their paths mean; the only general way
    to get a meaningful Handle is the Source.handles() method (or to make a
    copy of an existing one).

    Handles are serialisable and persistent, and two different Handles with the
    same type and properties compare equal."""

    type_label = None
    """A label that will be used to identify JSON forms of this Handle."""

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

    def to_json_object(self):
        """Returns an object suitable for JSON serialisation that represents
        this Handle."""
        return {
            "type": self.type_label,
            "source": self.get_source().to_json_object(),
            "path": self.get_relative_path()
        }

    __json_handlers = {}
    @staticmethod
    def json_handler(type_label):
        """Decorator: registers the decorated function as the handler for the
        type label given as an argument. This handler will be called by
        from_json_object when it finds this type label.

        Subclasses should use this method to decorate their from_json_object
        factory methods."""
        def _json_handler(func):
            if type_label in Handle.__json_handlers:
                raise ValueError(
                        "BUG: can't register two handlers" +
                        " for the same JSON type label!", type_label)
            Handle.__json_handlers[type_label] = func
            return func
        return _json_handler

    @staticmethod
    def stock_json_handler(type_label, constructor):
        return Handle.json_handler(type_label)(lambda obj: constructor(
                Source.from_json_object(obj["source"]), obj["path"]))

    @staticmethod
    def from_json_object(obj):
        """Converts a JSON representation of a Handle, as returned by the
        Handle.to_json_object method, back into a Handle."""
        try:
            tl = obj["type"]
            if not tl in Handle.__json_handlers:
                raise UnknownSchemeError(tl)
            return Handle.__json_handlers[tl](obj)
        except KeyError as k:
            tl = obj.get("type", None)
            raise DeserialisationError(tl, k.args[0])
