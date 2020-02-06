import re

from ..conversions.types import OutputType
from .rule import Rule, SimpleRule


class RegexRule(SimpleRule):
    operates_on = OutputType.Text
    type_label = "regex"
    eq_properties = ("_expression",)

    def __init__(self, expression):
        self._expression = expression
        self._compiled_expression = re.compile(expression)

    def match(self, content):
        if content is None:
            return

        for match in self._compiled_expression.finditer(content):
            yield {
                "offset": match.start(),
                "match": match.string[match.start():match.end()]
            }

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "expression": self._expression
        })

    @staticmethod
    @Rule.json_handler(type_label)
    def from_json_object(obj):
        return RegexRule(expression=obj["expression"])

    def __str__(self):
        return "RegexRule({0})".format(self._expression)
