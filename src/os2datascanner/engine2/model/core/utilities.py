from sys import stderr
from traceback import print_exc


class _SourceDescriptor:
    def __init__(self, *, source, parent=None):
        self.source = source
        self.parent = parent
        self.generator = None
        self.state = None
        self.children = []


class SourceManager:
    """A SourceManager is responsible for tracking all of the state associated
    with one or more Sources. Operations on Sources and Handles that require
    persistent state use a SourceManager to keep track of that state.

    When used as a context manager, a SourceManager will automatically clean up
    all of the state that it's been tracking at context exit time. This might
    mean, for example, automatically disconnecting from remote resources,
    unmounting drives, or closing file handles.

    As SourceManagers track (potentially process-specific) state, they are not
    usefully serialisable."""
    def __init__(self):
        """Initialises this SourceManager."""
        self._opened = {}
        self._opening = []

        # A synthetic _SourceDescriptor used as the parent for top-level
        # objects
        self._top = _SourceDescriptor(source=None)

    def _make_descriptor(self, source):
        return self._opened.setdefault(
                source, _SourceDescriptor(source=source, parent=self._top))

    def _reparent(self, child_d, parent_d):
        if (child_d.parent
                and child_d in child_d.parent.children):
            child_d.parent.children.remove(child_d)
        # Don't reparent to the dummy top element -- this case happens if the
        # path is incomplete, and actually doing it will throw away the
        # complete path
        if parent_d != self._top:
            child_d.parent = parent_d
        child_d.parent.children.append(child_d)

        # Also perform a dummy reparent operation all the way up the hierarchy
        # to ensure that the rightmost child is always the most recently used
        # one
        if parent_d.parent:
            self._reparent(parent_d, parent_d.parent)

    def _register_path(self, path):
        """Registers a path, a partial or complete reverse-ordered list of
        Sources of the form [child, parent, grandparent, ...], with this
        SourceManager. Paths are used to free resources in a sensible order.

        Paths are an internal implementation detail, and this function is
        intended for use only by SourceManager.open."""
        path = list(reversed(path))
        parent_d = self._top
        for child in path:
            child_d = self._make_descriptor(child)
            self._reparent(child_d, parent_d)
            parent_d = child_d
        return parent_d

    def open(self, source):
        """Returns the cookie returned by opening the given Source."""
        self._opening.append(source)
        self._register_path(self._opening)
        try:
            desc = self._make_descriptor(source)
            if not desc.generator:
                desc.generator = source._generate_state(self)
                desc.cookie = next(desc.generator)
                self._opened[source] = desc
            return desc.cookie
        finally:
            self._opening = self._opening[:-1]

    def close(self, source):
        """Closes a Source opened in this SourceManager, in the process closing
        all other open Sources that depend upon it."""
        if source in self._opened:
            desc = self._opened[source]

            if desc.children:
                # Clear up descendants of this Source
                for child in desc.children.copy():
                    self.close(child.source)
                desc.children.clear()

            if desc.generator:
                # Clear up the state and the generator
                desc.cookie = None
                try:
                    desc.generator.close()  # not allowed to fail
                except Exception:
                    stn = type(source).__name__
                    print("*** BUG: {0}._generate_state raised an exception!"
                            " Continuing anyway...".format(stn), file=stderr)
                    print_exc(file=stderr)

            if desc.parent:
                # Detach this Source from its parent
                desc.parent.children.remove(desc)
            del self._opened[source]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, backtrace):
        self.clear()

    def clear(self):
        """Closes all of the cookies returned by Sources that were opened in
        this SourceManager."""
        for child in self._top.children.copy():
            self.close(child.source)
