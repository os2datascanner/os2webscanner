import re
from datetime import datetime

from .rule import Rule, SimpleRule
from .types import InputType


DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


class LastModifiedRule(SimpleRule):
    operates_on = InputType.LastModified
    type_label = "last-modified"

    def __init__(self, after):
        self._after = after

    def match(self, content):
        if isinstance(content, str):
            content = datetime.strptime(content, DATE_FORMAT)
        if content > self._after:
            yield content.strftime(DATE_FORMAT)

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "after": self._after.strftime(DATE_FORMAT)
        })

    @staticmethod
    @Rule.json_handler(type_label)
    def from_json_object(obj):
        return LastModifiedRule(
                after=datetime.strptime(obj["after"], DATE_FORMAT))

    def __str__(self):
        return "LastModifiedRule({0})".format(self._after)
