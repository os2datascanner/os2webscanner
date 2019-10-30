from abc import ABC, abstractmethod

from ..model.core.errors import UnknownSchemeError, DeserialisationError


class JSONSerialisable(ABC):
    """Classes that extend the abstract base class JSONSerialisable can convert
    themselves to and from JSON-serialisable objects."""

    @property
    @classmethod
    @abstractmethod
    def _json_handlers(cls) -> dict:
        """A dictionary of the JSON handlers registered with this class.
        Immediate subclasses should implement this as a class attribute
        containing an empty dictionary."""
        pass

    @abstractmethod
    def to_json_object(self):
        """Returns an object suitable for JSON serialisation that represents
        this object."""

    @classmethod
    def json_handler(cls, type_label):
        """Decorator: registers the decorated function as the handler for the
        type label given as an argument. This handler will be called by
        from_json_object when it finds this type label.

        Subclasses should use this decorator to register their from_json_object
        factory methods."""
        def _json_handler(func):
            if type_label in cls._json_handlers:
                raise ValueError(
                        "BUG: can't register two handlers" +
                        " for the same JSON type label!", type_label)
            cls._json_handlers[type_label] = func
            return func
        return _json_handler

    @classmethod
    def from_json_object(cls, obj):
        """Converts a JSON representation of an object, as returned by the
        to_json_object method, back into an object."""
        try:
            tl = obj["type"]
            if not tl in cls._json_handlers:
                raise UnknownSchemeError(tl)
            return cls._json_handlers[tl](obj)
        except KeyError as k:
            tl = obj.get("type", None)
            raise DeserialisationError(tl, k.args[0])
