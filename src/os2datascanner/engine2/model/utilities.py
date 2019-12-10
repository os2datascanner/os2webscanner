from os import rmdir, remove
import os.path
from weakref import proxy, ProxyTypes
from tempfile import mkdtemp
from contextlib import suppress

class NamedTemporaryResource:
    def __init__(self, name):
        self._name = name
        self._dir = None

    def open(self, mode):
        return open(self.get_path(), mode)

    def get_path(self) -> str:
        if self._dir is None:
            self._dir = mkdtemp()
        return os.path.join(self._dir, self._name)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, backtrace):
        if self._dir:
            with suppress(FileNotFoundError):
                remove(self.get_path())
            with suppress(FileNotFoundError):
                rmdir(self._dir)
            self._dir = None


class MultipleResults(dict):
    """A MultipleResults is a subclass of dict that guarantees that all of the
    values it produces -- including default values -- are instances of the
    SingleResult class, and thus that they provide a (weak) reference back to
    the MultipleResults that contains them."""

    # Most of dict's methods are documented with a breezy "this just does
    # D[k]=F[k]", but this is only true if you *don't* override __setitem__,
    # so we need to do rather more work here than I might have liked...

    def __init__(self, what=None, **kwargs):
        super().__init__()
        self.update(what, **kwargs)

    def __setitem__(self, key, value):
        return super().__setitem__(key, self._wrap(key, value))

    def get(self, k, d=None):
        return super().get(k, self._wrap(k, d))

    def setdefault(self, k, d=None):
        return super().setdefault(k, self._wrap(k, d))

    def update(self, E=None, **F):
        if E:
            if hasattr(E, "keys"):
                for k in E:
                    self[k] = E[k]
            else:
                for k, v in E:
                    self[k] = v
        for k in F:
            self[k] = F[k]

    def _wrap(self, k, v):
        if v is None:
            return None
        elif isinstance(v, SingleResult):
            return SingleResult(self, k, v.value)
        else:
            return SingleResult(self, k, v)

    @classmethod
    def make_from_attrs(cls, o, *attrs, **kwargs):
        """Creates a new MultipleResults whose values correspond to all of the
        (extant) named attributes from a given object."""
        return cls({k: getattr(o, k) for k in attrs if hasattr(o, k)},
                **kwargs)


class SingleResult:
    """A SingleResult is a single value stored in a MultipleResults."""
    def __init__(self, parent, key, value):
        self._parent = None
        if parent is not None:
            if isinstance(parent, ProxyTypes):
                # Don't wrap proxies in proxies; weak references are confusing
                # enough as is!
                self._parent = parent
            else:
                self._parent = proxy(parent)
        self._key = key
        self._value = value

    @property
    def parent(self):
        """Returns a weakref.CallableProxyType for the parent
        MultipleResults, or None if none was specified."""
        return self._parent

    @property
    def key(self):
        """Returns the key associated with this SingleResult in the parent
        MultipleResults."""
        return self._key

    @property
    def value(self):
        """Returns the value associated with this SingleResult."""
        return self._value

    def map(self, f):
        """Returns a copy of this SingleResult, but with the value transformed
        by the given function. (The parent MultipleResults will *not* be
        updated.)"""
        return SingleResult(self.parent, self.key, f(self.value))
