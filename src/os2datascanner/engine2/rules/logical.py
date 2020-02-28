from abc import abstractmethod

from .rule import Rule, Sensitivity


class CompoundRule(Rule):
    def __init__(self, *components, sensitivity=None):
        super().__init__(sensitivity=sensitivity)
        self._components = components

    # It might have been nice to have a special implementation of
    # Rule.sensitivity here that finds the component with the highest
    # sensitivity and returns that, but that doesn't actually make sense: the
    # sensitivity of a CompoundRule is a function of the *matched* components,
    # not of all components considered out of context

    @classmethod
    @abstractmethod
    def make(cls, *components):
        """Creates a new Rule that represents the combination of all of the
        given components. The result does not need to be an instance of @cls:
        it could be a completely different kind of Rule, or a simple boolean
        value, if this rule can already be reduced to one.

        Subclasses must override this method, but should call up to this
        implementation."""
        if len(components) == 0:
            raise ValueError("CompoundRule with zero components")
        elif len(components) == 1:
            return components[0]
        else:
            return cls(*components)

    def split(self):
        fst, rest = self._components[0], self._components[1:]
        head, pve, nve = fst.split()
        return (head, self.make(pve, *rest), self.make(nve, *rest))

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "components": [c.to_json_object() for c in self._components]
        })


class AndRule(CompoundRule):
    """An AndRule is a CompoundRule corresponding to the C "&&" operator or the
    Python "and" operator (i.e., it has short-circuiting: as soon as one
    component reduces to False, no other components will be evaluated)."""

    type_label = "and"

    @classmethod
    def make(cls, *components):
        if False in components:
            return False
        else:
            return super().make(*[c for c in components if c is not True])

    @staticmethod
    @Rule.json_handler(type_label)
    def from_json_object(obj):
        return AndRule(
                *[Rule.from_json_object(o) for o in obj["components"]],
                sensitivity=Sensitivity.make_from_dict(obj))

    def __str__(self):
        return "AndRule({0})".format(
                ", ".join([str(r) for r in self._components]))

class OrRule(CompoundRule):
    """An AndRule is a CompoundRule corresponding to the C "||" operator or the
    Python "or" operator (i.e., it has short-circuiting: as soon as one
    component reduces to True, no other components will be evaluated)."""

    type_label = "or"

    @classmethod
    def make(cls, *components):
        if True in components:
            return True
        else:
            return super().make(*[c for c in components if c is not False])

    @staticmethod
    @Rule.json_handler(type_label)
    def from_json_object(obj):
        return OrRule(
                *[Rule.from_json_object(o) for o in obj["components"]],
                sensitivity=Sensitivity.make_from_dict(obj))

    def __str__(self):
        return "OrRule({0})".format(
                ", ".join([str(r) for r in self._components]))


class NotRule(Rule):
    type_label = "not"

    def __init__(self, rule, *, sensitivity=None):
        super().__init__(sensitivity=sensitivity)
        self._rule = rule

    @staticmethod
    def make(component):
        if component == True:
            return False
        elif component == False:
            return True
        elif isinstance(component, NotRule):
            return component._rule
        else:
            return NotRule(component)

    def split(self):
        rule, pve, nve = self._rule.split()
        return (rule, self.make(pve), self.make(nve))

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "rule": self._rule.to_json_object()
        })

    @staticmethod
    @Rule.json_handler(type_label)
    def from_json_object(obj):
        return NotRule(
                Rule.from_json_object(obj["rule"]),
                sensitivity=Sensitivity.make_from_dict(obj))

    def __str__(self):
        return "NotRule({0})".format(str(self._rule))


def make_if(predicate, then, else_):
    return OrRule.make(
            AndRule.make(predicate, then),
            AndRule.make(NotRule.make(predicate), else_))
