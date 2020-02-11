from sys import stderr
from traceback import print_exc


class _SourceDescriptor:
    def __init__(self, *, source):
        self.source = source
        self.generator = None
        self.state = None
        self.parent = None
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

    def _make_descriptor(self, source):
        return self._opened.setdefault(
                source, _SourceDescriptor(source=source))

    def _register_path(self, path):
        """Registers a path, a partial or complete reverse-ordered list of
        Sources of the form [child, parent, grandparent, ...], with this
        SourceManager. Paths are used to free resources in a sensible order.

        Paths are an internal implementation detail, and this function is
        intended for use only by SourceManager.open."""
        if len(path) > 1:
            # Convert the path [child, parent, grandparent, ..., ancestor K-1,
            # ancestor K] into a number of pairs of the form (ancestor K,
            # ancestor K-1), (ancestor K-1, ancestor K-2), ...,  (grandparent,
            # parent), (parent, child)
            for parent, child in zip(reversed(path), reversed(path[:-1])):
                parent_d = self._make_descriptor(parent)
                child_d = self._make_descriptor(child)

                child_d.parent = parent_d
                if child_d in parent_d.children:
                    parent_d.children.remove(child_d)
                parent_d.children.append(child_d)

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
                for child in desc.children.copy():
                    self.close(child.source)
                desc.children.clear()

            if desc.generator:
                desc.cookie = None
                try:
                    desc.generator.close()  # not allowed to fail
                except Exception:
                    stn = type(source).__name__
                    print("*** BUG: {0}._generate_state raised an exception!"
                            " Continuing anyway...".format(stn), file=stderr)
                    print_exc(file=stderr)

            if desc.parent:
                desc.parent.children.remove(desc)
            del self._opened[source]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, backtrace):
        self.clear()

    def clear(self):
        """Closes all of the cookies returned by Sources that were opened in
        this SourceManager."""
        opened = list(self._opened.keys())
        for source in opened:
            self.close(source)
