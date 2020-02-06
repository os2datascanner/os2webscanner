from ..conversions.types import OutputType
from .rule import Rule, SimpleRule


class LastModifiedRule(SimpleRule):
    operates_on = OutputType.LastModified
    type_label = "last-modified"

    def __init__(self, after):
        # Try encoding the given datetime.datetime as a JSON object; this will
        # raise a TypeError if something is wrong with it
        OutputType.LastModified.encode_json_object(after)
        self._after = after

    def match(self, content):
        if content > self._after:
            yield {
                "match": OutputType.LastModified.encode_json_object(content)
            }

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "after": OutputType.LastModified.encode_json_object(self._after)
        })

    @staticmethod
    @Rule.json_handler(type_label)
    def from_json_object(obj):
        return LastModifiedRule(
                after=OutputType.LastModified.decode_json_object(obj["after"]))

    def __str__(self):
        return "LastModifiedRule({0})".format(self._after)
