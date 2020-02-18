from enum import Enum
from datetime import datetime, timezone
from dateutil import tz


class OutputType(Enum):
    """Conversion functions return a typed result, and the type is a member of
    the OutputType enumeration. The values associated with these members are
    simple string identifiers that can be used in serialisation formats."""
    Text = "text" # str
    LastModified = "last-modified" # datetime.datetime
    ImageDimensions = "image-dimensions" # (int, int)

    Fallback = "fallback" # True
    Dummy = "dummy"

    def encode_json_object(self, v):
        """Converts an object (of the appropriate type for this OutputType) to
        a JSON-friendly representation."""
        if v == None:
            return None
        elif self == OutputType.Text:
            return str(v)
        elif self == OutputType.LastModified:
            return _datetime_to_str(v)
        elif self == OutputType.ImageDimensions:
            return [int(v[0]), int(v[1])]
        else:
            raise TypeError(self.value)

    def decode_json_object(self, v):
        """Constructs an object (of the appropriate type for this OutputType)
        from a JSON representation."""
        if v == None:
            return None
        elif self == OutputType.Text:
            return v
        elif self == OutputType.LastModified:
            return _str_to_datetime(v)
        elif self == OutputType.ImageDimensions:
            return (int(v[0]), int(v[1]))
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
    """Given a dictionary from OutputType values to objects, returns a new
    dictionary in which each of those objects has been converted to a
    JSON-friendly representation."""
    return {t: OutputType(t).encode_json_object(v) for t, v in d.items()}


def decode_dict(d):
    """Given a dictionary from OutputType values to JSON representations of
    objects, returns a new dictionary in which each of those representations
    has been converted back to an original object."""
    return {t: OutputType(t).decode_json_object(v) for t, v in d.items()}
