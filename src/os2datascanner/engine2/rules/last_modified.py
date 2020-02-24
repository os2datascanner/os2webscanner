from ..conversions.types import OutputType
from .rule import Rule, SimpleRule, Sensitivity


class LastModifiedRule(SimpleRule):
    operates_on = OutputType.LastModified
    type_label = "last-modified"

    def __init__(self, after, **super_kwargs):
        super().__init__(**super_kwargs)
        # Try encoding the given datetime.datetime as a JSON object; this will
        # raise a TypeError if something is wrong with it
        OutputType.LastModified.encode_json_object(after)
        self._after = after

    @property
    def presentation_raw(self):
        return "last modified after {0}".format(
                OutputType.LastModified.encode_json_object(self._after))

    def match(self, content):
        if content is None:
            return

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
                after=OutputType.LastModified.decode_json_object(obj["after"]),
                sensitivity=Sensitivity.make_from_dict(obj))
