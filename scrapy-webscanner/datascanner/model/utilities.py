from os import rmdir, remove
from pathlib import Path
from tempfile import mkdtemp

class NamedTemporaryResource:
    def __init__(self, name):
        self._name = name
        self._dir = None

    def open(self, mode):
        if not self._dir:
            self._dir = Path(mkdtemp())
        try:
            return open(self.get_path(), mode)
        except:
            raise

    def get_path(self):
        assert self._dir
        return self._dir.joinpath(self._name)

    def finished(self):
        assert self._dir
        remove(self.get_path())
        rmdir(self._dir)
        self._dir = None

class _TypPropEq:
    """\
Secret mixin! Classes inheriting from _TypPropEq compare equal if their types
and properties -- as determined by __getstate__() or __dict__ -- compare equal.
"""
    @staticmethod
    def __get_comparator(key):
        if hasattr(key, '__getstate__'):
            return key.__getstate__()
        else:
            return key.__dict__

    def __eq__(self, key):
        return type(self) == type(key) and \
                _TypPropEq.__get_comparator(self) == \
                _TypPropEq.__get_comparator(key)

    def __hash__(self):
        h = 42 + hash(type(self))
        for k, v in _TypPropEq.__get_comparator(self).items():
            h += hash(k) + (hash(v) * 3)
        return h

