from .core import (Source, Handle,
        Resource, FileResource, SourceManager, ResourceUnavailableError)
from .utilities import NamedTemporaryResource

import io
from os import stat_result, O_RDONLY
import email
from datetime import datetime
from contextlib import contextmanager
from exchangelib import Account, Credentials, IMPERSONATION, Configuration
from exchangelib.protocol import BaseProtocol
from exchangelib.errors import ErrorNonExistentMailbox


BaseProtocol.SESSION_POOLSIZE = 1


OFFICE_365_ENDPOINT = "https://outlook.office365.com/EWS/Exchange.asmx"


def _dictify_headers(headers):
    if headers:
        d = InsensitiveDict()
        for mh in headers:
            n, v = mh.name, mh.value
            if not n in d:
                d[n] = v
            else:
                if isinstance(d[n], list):
                    d[n].append(v)
                else:
                    d[n] = [d[n], v]
        return d
    else:
        return None


class InsensitiveDict(dict):
    def __getitem__(self, key):
        return super().__getitem__(key.lower())

    def __setitem__(self, key, value):
        return super().__setitem__(key.lower(), value)


class EWSAccountSource(Source):
    type_label = "ews"

    def __init__(self, domain, server, admin_user, admin_password, user):
        self._domain = domain
        self._server = server
        self._admin_user = admin_user
        self._admin_password = admin_password
        self._user = user

    def get_user(self):
        return self._user

    def get_domain(self):
        return self._domain

    def __str__(self):
        return "EWSSource({0}, {1}, {2}, ****, {3})".format(
                self._domain, self._server, self._admin_user, self._user)

    def _generate_state(self, sm):
        config = None
        service_account = Credentials(
                username=self._admin_user, password=self._admin_password)
        if self._server == OFFICE_365_ENDPOINT:
            config = Configuration(
                    service_endpoint=self._server,
                    credentials=service_account)

        address = "{0}@{1}".format(self._user, self._domain)
        try:
            account = Account(
                    primary_smtp_address=address,
                    credentials=service_account,
                    config=config,
                    autodiscover=not bool(config),
                    access_type=IMPERSONATION)
        except ErrorNonExistentMailbox as e:
            raise ResourceUnavailableError(self, e.args)

        try:
            yield account
        finally:
            pass # account.protocol.close()

    def handles(self, sm):
        account = sm.open(self)

        def relevant_folders():
            for container in account.root.walk():
                if (container.folder_class != "IPF.Note"
                        or container.total_count == 0):
                    continue
                yield container

        def relevant_mails(relevant_folders):
            for folder in relevant_folders:
                for mail in folder.all().only("id", "headers"):
                    headers = _dictify_headers(mail.headers)
                    if headers:
                        yield EWSMailHandle(self,
                                "{0}.{1}".format(folder.id, mail.id),
                                headers["subject"])

        yield from relevant_mails(relevant_folders())

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "domain": self._domain,
            "server": self._server,
            "admin_user": self._admin_user,
            "admin_password": self._admin_password,
            "user": self._user
        })

    @staticmethod
    @Source.json_handler(type_label)
    def from_json_object(obj):
        return EWSSource(
                obj["domain"], obj["server"], obj["admin_user"],
                obj["admin_password"], obj["user"])


MAIL_MIME = "application/x-os2datascanner-mailhandle"


class EWSMailHandle(Handle):
    type_label = "ews"

    def __init__(self, source, path, mail_subject):
        super().__init__(source, path)
        self._mail_subject = mail_subject

    @property
    def representation(self):
        return "\"{0}\" (in {1}@{2})".format(self._mail_subject,
                self.get_source().get_user(), self.get_source().get_domain())

    def __str__(self):
        return self.representation

    def follow(self, sm):
        return EWSMailResource(self, sm)

    def guess_type(self):
        return MAIL_MIME


class EWSMailResource(Resource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._ids = self.get_handle().get_relative_path().split(
                ".", maxsplit=1)
        self._message = None

    def get_message_object(self):
        if not self._message:
            folder_id, mail_id = self._ids
            account = self._get_cookie()
            self._message = account.root.get_folder(folder_id).get(id=mail_id)
        return self._message

    def get_email_message(self):
        return email.message_from_string(
                self.get_message_object().mime_content)

    def compute_type(self):
        return MAIL_MIME


@Source.mime_handler(MAIL_MIME)
class MailSource(Source):
    type_label = "mail"

    def __init__(self, mh):
        self._handle = mh

    def to_handle(self):
        return self._handle

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

    def to_json_object(self):
        return dict(**super().to_json_object, **{
            "handle": self.to_handle().to_json_object()
        })

    @staticmethod
    @Source.json_handler(type_label)
    def from_json_object(obj):
        return MailSource(Handle.from_json_object(obj))


class MailPartHandle(Handle):
    type_label = "mail-part"

    def __init__(self, source, path, mime):
        super().__init__(source, path)
        self._mime = mime

    @property
    def presentation(self):
        return "{0} (in {1})".format(
                self.get_name(), self.get_source().get_handle())

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
        yield io.BytesIO(self._get_fragment().get_payload(decode=True))
