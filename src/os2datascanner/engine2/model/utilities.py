from os import rmdir, remove
from pathlib import Path
from tempfile import mkdtemp

class NamedTemporaryResource:
    def __init__(self, name):
        self._name = name
        self._dir = None

    def open(self, mode):
        if self._dir is None:
            self._dir = Path(mkdtemp())
        try:
            return self.get_path().open(mode)
        except:
            raise

    def get_path(self) -> Path:
        return self._dir.joinpath(self._name)

    def finished(self):
        self.get_path().unlink()
        self._dir.rmdir()
        self._dir = None

class _TypPropEq:
    """Secret mixin! Classes inheriting from _TypPropEq compare equal if their
    types and properties compare equal.

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
        return (type(self) == type(other) and
                self.__get_state(self) == self.__get_state(other))

    def __hash__(self):
        h = 42 + hash(type(self))
        for k, v in self.__get_state(self).items():
            h += hash(k) + (hash(v) * 3)
        return h

