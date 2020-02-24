from abc import abstractmethod
from enum import Enum
from typing import Union, Optional

from ..utilities.json import JSONSerialisable
from ..utilities.equality import TypePropertyEquality
from ..conversions.types import OutputType


class Sensitivity(Enum):
    """Rules have an optional property called "sensitivity", whose values are
    given by the Sensitivity enumeration. This property has no particular
    significance for the rule engine, but user interfaces might wish to present
    matches differently based on it."""
    INFORMATION = 0
    NOTICE = 250
    WARNING = 500
    PROBLEM = 750
    CRITICAL = 1000

    @staticmethod
    def make_from_dict(obj):
        if "sensitivity" in obj and obj["sensitivity"] is not None:
            return Sensitivity(obj["sensitivity"])
        else:
            return None


class Rule(TypePropertyEquality, JSONSerialisable):
    """A Rule represents a test to be applied to a representation of an
    object.

    Rules cannot necessarily be evaluated directly, but they can always be
    broken apart to find an evaluable component; see the split() method.

    If you're not sure which class your new rule should inherit from, then use
    SimpleRule."""

    def __init__(self, *, sensitivity=None, name=None):
        self._sensitivity = sensitivity
        self._name = name

    @property
    def presentation(self) -> str:
        """Returns a (perhaps localised) human-readable string representing
        this Rule, for use in user interfaces."""
        return self._name

    @property
    def sensitivity(self) -> Optional[Sensitivity]:
        """Returns the sensitivity value of this Rule, if one was specified."""
        return self._sensitivity

    @property
    @abstractmethod
    def type_label(self) -> str:
        """A label that will be used to identify JSON forms of this Rule."""

    @abstractmethod
    def split(self) -> ('SimpleRule',
            Union['SimpleRule', bool], Union['SimpleRule', bool]):
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
            "type": self.type_label,
            "sensitivity": self.sensitivity.value if self.sensitivity else None
        }

    def __str__(self):
        return self.presentation


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
        """Yields zero or more dictionaries suitable for JSON serialisation,
        each of which represents one match of this SimpleRule against the
        provided content. Matched content should appear under the dictionary's
        "match" key."""
