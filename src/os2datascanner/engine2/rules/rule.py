from abc import ABC, abstractmethod

from .types import InputType

class Rule(ABC):
    """A Rule represents a test to be applied to a representation of an object.
    Rules declare of what type they expect that representation to be; working
    out how to convert arbitrary objects to that type is left to the caller."""

    @property
    @abstractmethod
    def operates_on():
        """The type of input expected by this Rule."""
        return InputType.Text

    @property
    @abstractmethod
    def type_label():
        """A label that will be used to identify JSON forms of this Rule."""

    @abstractmethod
    def match(self, content):
        """Returns an iterable of zero or more objects suitable for JSON
        serialisation, each of which represents one match of this Rule against
        the provided content. (An empty sequence represents no matches.)"""

    @abstractmethod
    def to_json_object(self):
        """Returns an object suitable for JSON serialisation that represents
        this Rule."""
        return {
            "type": self.type_label
        }

    __json_handlers = {}
    @staticmethod 
    def json_handler(type_label):
        def _json_handler(func):
            if type_label in Rule.__json_handlers:
                raise ValueError(
                        "BUG: can't register two handlers" +
                        " for the same JSON type label!", type_label)
            Rule.__json_handlers[type_label] = func
            return func
        return _json_handler

    @staticmethod
    def from_json_object(obj):
        """Converts a JSON representation of a Rule, as returned by the
        Rule.to_json_object method, back into a Rule."""
        try:
            return Rule.__json_handlers[obj["type"]](obj)
        except KeyError:
            # XXX: better error handling would probably be a good idea
            raise
