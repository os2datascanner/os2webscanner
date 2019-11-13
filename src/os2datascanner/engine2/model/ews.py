from .core import Source, Handle, Resource, ResourceUnavailableError

import io
from os import stat_result, O_RDONLY
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


class EWSSource(Source):
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
            account.protocol.close()

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
                for mail in folder.all():
                    headers = _dictify_headers(mail.headers)
                    if headers:
                        yield EWSHandle(self,
                                "{0}.{1}".format(folder.id, mail.id),
                                folder.name, headers["subject"])

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


class EWSHandle(Handle):
    type_label = "ews"

    def __init__(self, source, path, folder_name, mail_subject):
        super().__init__(source, path)
        self._folder_name = folder_name
        self._mail_subject = mail_subject

    @property
    def representation(self):
        return "\"{0}\" (in {1}@{2})".format(self._mail_subject,
                self.get_source().get_user(), self.get_source().get_domain())

    def __str__(self):
        return self.representation

    def follow(self, sm):
        raise NotImplementedError("EWSHandle.follow")
