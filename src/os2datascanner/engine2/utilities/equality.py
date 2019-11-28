class TypePropertyEquality:
    """Classes inheriting from the TypePropertyEquality mixin compare equal if
    their type objects and properties compare equal.

    The relevant properties for this purpose are, in order of preference:
    - those enumerated by the 'eq_properties' field;
    - the keys of the dictionary returned by its __getstate__ function; or
    - the keys of its __dict__ field."""
    @staticmethod
    def __get_state(obj):
        if hasattr(obj, 'eq_properties'):
            return {k: getattr(obj, k) for k in getattr(obj, 'eq_properties')}
        elif hasattr(obj, '__getstate__'):
            return obj.__getstate__()
        else:
            return obj.__dict__

    def __eq__(self, other):
        print("{0}.__eq__({1})?".format(
                self.__get_state(self), self.__get_state(other))
        return (type(self) == type(other) and
                self.__get_state(self) == self.__get_state(other))

    def __hash__(self):
        h = 42 + hash(type(self))
        for k, v in self.__get_state(self).items():
            h += hash(k) + (hash(v) * 3)
        return h

