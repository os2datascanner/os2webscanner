from ..conversions.types import OutputType
from .rule import Rule, SimpleRule, Sensitivity


class HasConversionRule(SimpleRule):
    type_label = "conversion"

    def __init__(self, target, **super_kwargs):
        super().__init__(**super_kwargs)
        self._target = target

    @property
    def presentation_raw(self):
        return "convertible to {0}".format(self._target.value)

    @property
    def operates_on(self):
        return self._target

    def match(self, content):
        if content is None:
            return

        try:
            self._target.encode_json_object(content)
            yield {
                "match": self._target.value
            }
        except TypeError:
            pass

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "target": self._target.value
        })

    @staticmethod
    @Rule.json_handler(type_label)
    def from_json_object(obj):
        return HasConversionRule(
                target=OutputType(obj["target"]),
                sensitivity=Sensitivity.make_from_dict(obj),
                name=obj["name"] if "name" in obj else None)
