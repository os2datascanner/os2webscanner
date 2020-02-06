from enum import Enum
from datetime import datetime, timezone
from dateutil import tz


class InputType(Enum):
    """Rules declare what type they expect to operate on by specifying a member
    of the InputType enumeration. The values associated with these members are
    simple string identifiers that can be used in serialisation formats."""
    Text = "text" # str
    LastModified = "last-modified" # datetime.datetime

    def encode_json_object(self, v):
        """Converts an object (of the appropriate type for this InputType) to
        a JSON-friendly representation."""
        if self == InputType.Text:
            return str(v)
        elif self == InputType.LastModified:
            return _datetime_to_str(v)
        else:
            raise TypeError(self.value)

    def decode_json_object(self, v):
        """Constructs an object (of the appropriate type for this InputType)
        from a JSON representation."""
        if self == InputType.Text:
            return v
        elif self == InputType.LastModified:
            return _str_to_datetime(v)
        else:
            raise TypeError(self.value)


DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def _datetime_to_str(d):
    if not d.tzinfo:
        raise TypeError(
                "Only timezone-aware datetime.datetime objects can be"
                " serialised")
    return d.strftime(DATE_FORMAT)


def _str_to_datetime(s):
    return datetime.strptime(s, DATE_FORMAT)


def encode_dict(d):
    """Given a dictionary from InputType values to objects, returns a new
    dictionary in which each of those objects has been converted to a
    JSON-friendly representation."""
    return {t: InputType(t).encode_json_object(v) for t, v in d.items()}


def decode_dict(d):
    """Given a dictionary from InputType values to JSON representations of
    objects, returns a new dictionary in which each of those representations
    has been converted back to an original object."""
    return {t: InputType(t).decode_json_object(v) for t, v in d.items()}
