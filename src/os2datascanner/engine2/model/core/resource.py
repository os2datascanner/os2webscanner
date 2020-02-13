from abc import ABC, abstractmethod
import magic
from datetime import datetime

from ...conversions.types import OutputType
from ...conversions.utilities.results import SingleResult, MultipleResults


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


class TimestampedResource(Resource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._lm_timestamp = None

    @abstractmethod
    def get_last_modified(self):
        """Returns the last modification date of this TimestampedResource as a
        wrapped Python datetime.datetime; this may be used to decide whether or
        not a FileResource's content should be re-examined. Multiple calls to
        this method should normally return the same value.

        The default implementation of this method returns the time this
        method was first called on this TimestampedResource."""
        if not self._lm_timestamp:
            self._lm_timestamp = SingleResult(
                    None, OutputType.LastModified, datetime.now())
        return self._lm_timestamp


class FileResource(TimestampedResource):
    """A FileResource is a TimestampedResource that can be viewed as a file: a
    sequence of bytes with a size."""
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


MAIL_MIME = "message/rfc822"
"""A special MIME type for explorable emails. Resources (and their associated
Handles) that represent an email message, and that have a get_email_message
function that returns the content of that message as a Python email.message.
EmailMessage, should report this type in order to be automatically
explorable."""


class MailResource(TimestampedResource):
    """A MailResource is a TimestampedResource that can be viewed as an email:
    a message body accompanied by a number of headers."""

    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._mr = None
        self._lm_timestamp = None

    def unpack_headers(self):
        if not self._mr:
            self._mr = MultipleResults()
            m = self.get_email_message()
            for k in m.keys():
                v = m.get_all(k)
                if v and len(v) == 1:
                    v = v[0]
                self._mr[k.lower()] = v
            date = self._mr.get("date")
            if date and date.value.datetime:
                self._mr[OutputType.LastModified] = date.value.datetime
        return self._mr

    @abstractmethod
    def get_email_message(self):
        """Returns a structured representation of this email as a Python
        email.message.EmailMessage."""

    def get_last_modified(self):
        return self.unpack_headers().get(OutputType.LastModified,
                super().get_last_modified())

    def compute_type(self):
        return MAIL_MIME
