"""Base classes for rules."""


class Rule:

    """Represents a rule which can be executed on text and returns matches."""

    def execute(self, text):
        """Execute the rule on the given text.

        Return a list of MatchItem's.
        """
        raise NotImplementedError
