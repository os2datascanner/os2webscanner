import email
import email.policy
import chardet
from datetime import datetime
from exchangelib import Account, Credentials, IMPERSONATION, Configuration
from exchangelib.protocol import BaseProtocol
from exchangelib.errors import ErrorNonExistentMailbox

from .core import (
        Source, Handle, MailResource, SourceManager, ResourceUnavailableError)
from .core.resource import MAIL_MIME


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

    @property
    def user(self):
        return self._user

    @property
    def domain(self):
        return self._domain

    @property
    def address(self):
        return "{0}@{1}".format(self.user, self.domain)

    def _generate_state(self, sm):
        config = None
        service_account = Credentials(
                username=self._admin_user, password=self._admin_password)
        if self._server is not None:
            config = Configuration(
                    service_endpoint=self._server,
                    credentials=service_account)

        try:
            account = Account(
                    primary_smtp_address=self.address,
                    credentials=service_account,
                    config=config,
                    autodiscover=not bool(config),
                    access_type=IMPERSONATION)
        except ErrorNonExistentMailbox as e:
            raise ResourceUnavailableError(self, e.args)

        try:
            yield account
        finally:
            # XXX: we should, in principle, close account.protocol here, but
            # exchangelib seems to keep a reference to it internally and so
            # waits forever if we do
            pass

    def censor(self):
        return EWSAccountSource(
                self._domain, self._server, None, None, self._user)

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
        return EWSAccountSource(
                obj["domain"], obj["server"], obj["admin_user"],
                obj["admin_password"], obj["user"])


class EWSMailResource(MailResource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._ids = self.handle.relative_path.split(".", maxsplit=1)
        self._message = None

    def get_message_object(self):
        if not self._message:
            folder_id, mail_id = self._ids
            account = self._get_cookie()
            self._message = account.root.get_folder(folder_id).get(id=mail_id)
        return self._message

    def get_email_message(self):
        msg = self.get_message_object().mime_content
        if isinstance(msg, bytes):
            # exchangelib seems not to (be able to?) give us any clues about
            # message encoding, so try using chardet to work out what this is
            detected = chardet.detect(msg)
            msg = msg.decode(detected["encoding"])
        return email.message_from_string(msg, policy=email.policy.default)

    def compute_type(self):
        return MAIL_MIME


class EWSMailHandle(Handle):
    type_label = "ews"
    resource_type = EWSMailResource

    # The mail subject is useful for presentation purposes, but not important
    # when computing equality
    eq_properties = Handle.BASE_PROPERTIES

    def __init__(self, source, path, mail_subject):
        super().__init__(source, path)
        self._mail_subject = mail_subject

    @property
    def presentation(self):
        return "\"{0}\" (in account {1})".format(
                self._mail_subject, self.source.address)

    def censor(self):
        return EWSMailHandle(
                self.source.censor(), self.relative_path, self._mail_subject)

    def guess_type(self):
        return MAIL_MIME

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "mail_subject": self._mail_subject
        })

    @staticmethod
    @Handle.json_handler(type_label)
    def from_json_object(obj):
        return EWSMailHandle(Source.from_json_object(obj["source"]),
                obj["path"], obj["mail_subject"])
