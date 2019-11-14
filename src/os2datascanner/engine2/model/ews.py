from .core import (Source, Handle,
        Resource, FileResource, SourceManager, ResourceUnavailableError)
from .special.mail import MIME_TYPE as MAIL_MIME

import email
from datetime import datetime
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
        return EWSAccountSource(
                obj["domain"], obj["server"], obj["admin_user"],
                obj["admin_password"], obj["user"])


class EWSMailHandle(Handle):
    type_label = "ews"

    # The mail subject is useful for presentation purposes, but not important
    # when computing equality
    eq_properties = Handle.BASE_PROPERTIES

    def __init__(self, source, path, mail_subject):
        super().__init__(source, path)
        self._mail_subject = mail_subject

    @property
    def presentation(self):
        return "\"{0}\" (in {1}@{2})".format(self._mail_subject,
                self.get_source().get_user(), self.get_source().get_domain())

    def follow(self, sm):
        return EWSMailResource(self, sm)

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
