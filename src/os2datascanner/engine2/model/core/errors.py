class UnknownSchemeError(LookupError):
    """When Source.from_url does not know how to handle a given URL, either
    because no Source subclass is registered as a handler for its scheme or
    because the URL is not valid, an UnknownSchemeError will be raised.
    Its only associated value is a string identifying the scheme, if one was
    present in the URL.

    An UnknownSchemeError can also be raised by the JSON deserialisation code
    if no handler exists for an object's type label; in these circumstances,
    the single associated value is the type label."""

class DeserialisationError(KeyError):
    """When converting a JSON representation of an object back into an object,
    if a required property is missing or has a nonsensical value, a
    DeserialisationError will be raised. It has two associated values: the
    type of object being deserialised, if known, and the property at issue."""

class ResourceUnavailableError(Exception):
    """When a method of a Source or Resource (or of one of their subclasses)
    fails to access an object, a ResourceUnavailableError will be raised. The
    first associated value will be the Source, or the Handle of the Resource,
    that triggered the error; subsequent values, if present, give specific
    details of the failure."""

    def __str__(self):
        hand, args = self.args[0], self.args[1:]
        if args:
            return "ResourceUnavailableError({0}, {1})".format(
                    hand, ", ".join([str(arg) for arg in args]))
        else:
            return "ResourceUnavailableError({0})".format(hand)
