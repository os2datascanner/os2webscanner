from abc import ABC, abstractmethod
import magic
from datetime import datetime

from ...rules.types import InputType
from ..utilities import SingleResult


class Resource(ABC):
    """A Resource is a concrete embodiment of an object: it's the thing a
    Handle points to. If you have a Resource, then you have some way of getting
    to the data (and metadata) behind a Handle. Most kinds of Resource behave,
    or can behave, like files; these are represented by the FileResource
    subclass.

    Resources normally have functions that retrieve individual property values
    from an object. To minimise wasted computation, these values are wrapped in
    the SingleResult class, which allows them to include by reference other
    values that were computed at the same time.

    Resources are short-lived -- they should only be used when you actually
    need to get to content. As such, they are not serialisable."""
    def __init__(self, handle, sm):
        self._handle = handle
        self._sm = sm

    @property
    def handle(self):
        """Returns this Resource's Handle."""
        return self._handle

    def _get_cookie(self):
        """Returns the magic cookie produced when the Source behind this
        Resource's Handle is opened in the associated StateManager. (Note that
        each Source will only be opened once by a given StateManager.)"""
        return self._sm.open(self.handle.source)


class FileResource(Resource):
    """A FileResource is a Resource that can, when necessary, be viewed as a
    file."""
    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._lm_timestamp = None

    @abstractmethod
    def get_size(self):
        """Returns the wrapped number of bytes advertised as the download size
        of this FileResource's content. (Note that this is not necessarily the
        same as the *actual* size of that content: some Sources support
        transparent compression and decompression.)"""

    @abstractmethod
    def get_last_modified(self):
        """Returns the last modification date of this FileResource as a wrapped
        Python datetime.datetime; this may be used to decide whether or not a
        FileResource's content should be re-examined. Multiple calls to this
        method should normally return the same value.

        The default implementation of this method returns the time this
        method was first called on this FileResource."""
        if not self._lm_timestamp:
            self._lm_timestamp = SingleResult(
                    None, InputType.LastModified, datetime.now())
        return self._lm_timestamp

    @abstractmethod
    def make_path(self):
        """Returns a context manager that, when entered, returns a path through
        which the content of this FileResource can be accessed until the
        context is exited. (Do not attempt to write to this path -- the result
        is undefined.)"""

    @abstractmethod
    def make_stream(self):
        """Returns a context manager that, when entered, returns a read-only
        Python stream through which the content of this FileResource can be
        accessed until the context is exited."""

    def compute_type(self):
        """Guesses the type of this file, possibly examining its content in the
        process. By default, this is computed by giving libmagic the first 512
        bytes of the file."""
        with self.make_stream() as s:
            return magic.from_buffer(s.read(512), True)
