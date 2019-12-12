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


def adapt_datetime(d=None):
    """Converts a datetime.datetime (by default, the current time) to a form
    suitable for unambiguous representation in ISO 8601 extended format, with
    a simple timezone offset and no microseconds."""
    if not d:
        d = datetime.now()
    if not d.tzinfo:
        d = d.replace(tzinfo=timezone(tz.gettz().utcoffset(d)))
    return d.replace(microsecond=0)


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


__converters = {}


def conversion(input_type, *mime_types):
    """Decorator: registers the decorated function as the converter of each of
    the specified MIME types to the specified InputType."""
    def _conversion(f):
        for m in mime_types:
            k = (input_type, m)
            if k in __converters:
                raise ValueError(
                        "BUG: can't register two handlers" +
                        " for the same (InputType, MIME type) pair!", k)
            __converters[k] = f
        return f
    return _conversion


def conversion_exists(input_type, mime_type):
    """Indicates whether or not a conversion function is registered for the
    given pair of input type and MIME type."""
    return (input_type, mime_type) in __converters


def convert(resource, input_type, mime_override=None):
    """Tries to convert a Resource to the specified InputType by using the
    database of registered conversion functions."""
    mime_type = resource.compute_type() if not mime_override else mime_override
    try:
        return __converters[(input_type, mime_type)](resource)
    except KeyError:
        return None
