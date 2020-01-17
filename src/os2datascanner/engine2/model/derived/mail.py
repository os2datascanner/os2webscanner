from io import BytesIO
from contextlib import contextmanager

from ..core import Source, Handle, FileResource, SourceManager
from ..core.resource import MAIL_MIME
from ..utilities import SingleResult, NamedTemporaryResource
from .derived import DerivedSource


@Source.mime_handler(MAIL_MIME)
class MailSource(DerivedSource):
    type_label = "mail"

    def _generate_state(self, sm):
        yield self.handle.follow(sm).get_email_message()

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


class MailPartResource(FileResource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._fragment = None

    def _get_fragment(self):
        if not self._fragment:
            where = self._get_cookie()
            path = self.handle.relative_path.split("/")[:-1]
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
                return SingleResult(None, "size", s.tell())
            finally:
                s.seek(initial, 0)

    @contextmanager
    def make_path(self):
        with NamedTemporaryResource(self.handle.name) as ntr:
            with ntr.open("wb") as res:
                with self.make_stream() as s:
                    res.write(s.read())
            yield ntr.get_path()

    @contextmanager
    def make_stream(self):
        yield BytesIO(self._get_fragment().get_payload(decode=True))


class MailPartHandle(Handle):
    type_label = "mail-part"
    resource_type = MailPartResource

    def __init__(self, source, path, mime):
        super().__init__(source, path)
        self._mime = mime

    @property
    def presentation(self):
        return "{0} (in {1})".format(self.name, self.source.handle)

    def censor(self):
        return MailPartHandle(
                self.source.censor(), self.relative_path, self._mime)

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
