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
