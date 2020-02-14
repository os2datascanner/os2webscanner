from abc import abstractmethod

from ..utilities.json import JSONSerialisable
from ..utilities.equality import TypePropertyEquality
from ..conversions.types import OutputType


class Rule(TypePropertyEquality, JSONSerialisable):
    """A Rule represents a test to be applied to a representation of an
    object.

    Rules cannot necessarily be evaluated directly, but they can always be
    broken apart to find an evaluable component; see the split() method.

    If you're not sure which class your new rule should inherit from, then use
    SimpleRule."""

    @property
    @abstractmethod
    def type_label(self) -> str:
        """A label that will be used to identify JSON forms of this Rule."""

    @abstractmethod
    def split(self):
        """Splits this Rule.

        Splitting a Rule produces a SimpleRule, suitable for immediate
        evaluation, and two continuation Rules. The first of these, the
        positive continuation, is the Rule that should be executed next if the
        SimpleRule finds a match; the second, the negative continuation, should
        be executed if no match was found.

        (Following a chain of continuations will always eventually reduce to
        True, if the rule as a whole has matched, or False if it has not.)"""

    _json_handlers = {}

    @abstractmethod
    def to_json_object(self):
        """Returns an object suitable for JSON serialisation that represents
        this Rule."""
        return {
            "type": self.type_label
        }


class SimpleRule(Rule):
    """A SimpleRule is a rule that can be evaluated. Splitting it produces the
    trivial positive and negative continuations True and False.

    If you're not sure which class your new rule should inherit from, then use
    this one."""
    def split(self):
        return (self, True, False)

    @property
    @abstractmethod
    def operates_on(self) -> OutputType:
        """The type of input expected by this SimpleRule."""

    @abstractmethod
    def match(self, content):
        """Returns an iterable of zero or more objects suitable for JSON
        serialisation, each of which represents one match of this SimpleRule
        against the provided content. (An empty iterable represents no
        matches.)"""
