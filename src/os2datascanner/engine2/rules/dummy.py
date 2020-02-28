from ..conversions.types import OutputType
from .rule import Rule, SimpleRule, Sensitivity


class DummyRule(SimpleRule):
    """DummyRule matches nothing: it returns no results for any content, and it
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
        return DummyRule(sensitivity=Sensitivity.make_from_dict(obj))


class FallbackRule(SimpleRule):
    """FallbackRule matches everything: it unconditionally returns True as a
    match for every input, and it operates on an OutputType which defines a
    single trivial conversion from every input object to True.

    It can be used to define a fallback branch for OrRules, which is chiefly
    useful when using sensitivity values. Consider, for example, a rule of the
    following form:

    AndRule(
        CPRRule(),
        OrRule(
            AndRule(
                NameRule(),
                AddressRule(),
                sensitivity=Sensitivity.CRITICAL),
            OrRule(
                NameRule(),
                AddressRule(),
                sensitivity=Sensitivity.PROBLEM),
            FallbackRule(sensitivity=Sensitivity.WARNING)))

    This rule expresses the logic "if an object's text representation contains
    a CPR number, then check for a name and an address. If both of those are
    present, the match is CRITICAL; if at most one is present, the match is
    a PROBLEM; and if neither of those is present, the match is a WARNING".
    Without FallbackRule, there would be no way to express the last case."""

    operates_on = OutputType.Fallback
    type_label = "fallback"

    def match(self, content):
        yield {
            "match": True
        }

    def to_json_object(self):
        return super().to_json_object()

    @staticmethod
    @Rule.json_handler(type_label)
    def from_json_object(obj):
        return FallbackRule(sensitivity=Sensitivity.make_from_dict(obj))
