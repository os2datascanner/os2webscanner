from .rule import Rule, SimpleRule
from .types import InputType


class LastModifiedRule(SimpleRule):
    operates_on = InputType.LastModified
    type_label = "last-modified"

    def __init__(self, after):
        # Try encoding the given datetime.datetime as a JSON object; this will
        # raise a TypeError if something is wrong with it
        InputType.LastModified.encode_json_object(after)
        self._after = after

    def match(self, content):
        if content > self._after:
            yield {
                "match": InputType.LastModified.encode_json_object(content)
            }

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "after": InputType.LastModified.encode_json_object(self._after)
        })

    @staticmethod
    @Rule.json_handler(type_label)
    def from_json_object(obj):
        return LastModifiedRule(
                after=InputType.LastModified.decode_json_object(obj["after"]))

    def __str__(self):
        return "LastModifiedRule({0})".format(self._after)
