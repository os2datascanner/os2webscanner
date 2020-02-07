from ..conversions.types import OutputType
from .rule import Rule, SimpleRule


class DummyRule(SimpleRule):
    """DummyRule does nothing. It returns no results for any content, and it
    claims to operate on an OutputType for which no conversions are defined.

    It can be used to force the pipeline to completely explore a Source without
    actually performing any other work along the way."""

    operates_on = OutputType.Dummy
    type_label = "dummy"

    def match(self, content):
        yield from []

    def to_json_object(self):
        return super().to_json_object()

    @staticmethod
    @Rule.json_handler(type_label)
    def from_json_object(obj):
        return DummyRule()
