from io import BytesIO
from contextlib import contextmanager

from ..core import Source, Handle, FileResource, DerivedSource, SourceManager
from ..utilities import NamedTemporaryResource


MIME_TYPE = "message/rfc822"
"""A special MIME type for explorable emails. Resources (and their associated
Handles) that represent an email message, and that have a to_email_message
function that returns the content of that message as a Python
email.message.Message, should report this type in order to be automatically
explorable."""


@Source.mime_handler(MIME_TYPE)
class MailSource(DerivedSource):
    type_label = "mail"

    def _generate_state(self, sm):
        with SourceManager(sm) as sm:
            yield self.to_handle().follow(sm).get_email_message()

    def handles(self, sm):
        def _process_message(path, part):
            ct = part.get_content_maintype()
            if ct == "multipart":
                for idx, fragment in enumerate(part.get_payload()):
                    yield from _process_message(path + [str(idx)], fragment)
            else:
                filename = part.get_filename()
                full_path = "/".join(path + [filename or ''])
                yield MailPartHandle(self, full_path, part.get_content_type())
        yield from _process_message([], sm.open(self))

    @staticmethod
    @Source.json_handler(type_label)
    def from_json_object(obj):
        return MailSource(Handle.from_json_object(obj["handle"]))


class MailPartHandle(Handle):
    type_label = "mail-part"

    def __init__(self, source, path, mime):
        super().__init__(source, path)
        self._mime = mime

    @property
    def presentation(self):
        return "{0} (in {1})".format(
                self.get_name(), self.get_source().to_handle())

    def follow(self, sm):
        return MailPartResource(self, sm)

    def guess_type(self):
        return self._mime

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "mime": self._mime
        })

    @staticmethod
    @Handle.json_handler(type_label)
    def from_json_object(obj):
        return MailPartHandle(Source.from_json_object(obj["source"]),
                obj["path"], obj["mime"])


class MailPartResource(FileResource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._fragment = None

    def _get_fragment(self):
        if not self._fragment:
            where = self._get_cookie()
            path = self.get_handle().get_relative_path().split("/")[:-1]
            while path:
                next_idx, path = int(path[0]), path[1:]
                where = where.get_payload()[next_idx]
            self._fragment = where
        return self._fragment

    def get_last_modified(self):
        return super().get_last_modified()

    def get_size(self):
        with self.make_stream() as s:
            initial = s.seek(0, 1)
            try:
                s.seek(0, 2)
                return s.tell()
            finally:
                s.seek(initial, 0)

    @contextmanager
    def make_path(self):
        ntr = NamedTemporaryResource(self.get_handle().get_name())
        try:
            with ntr.open("wb") as res:
                with self.make_stream() as s:
                    res.write(s.read())
            yield ntr.get_path()
        finally:
            ntr.finished()

    @contextmanager
    def make_stream(self):
        yield BytesIO(self._get_fragment().get_payload(decode=True))
