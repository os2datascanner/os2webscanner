import os
import sys
from exchangelib import FileAttachment, ItemAttachment
from exchangelib import IMPERSONATION, Credentials, Account
import password


class ExchangeScan(object):
    """ Library to export a users mailbox from Exchange to a filesystem """
    def __init__(self, user):
        credentials = Credentials(username="mailscan",
                                  password=password.password)
        username = user + "@vordingborg.dk"
        self.folder = 'users/' + username
        self.account = Account(primary_smtp_address=username,
                               credentials=credentials, autodiscover=True,
                               access_type=IMPERSONATION)

    def total_mails(self):
        """ Return the total amounts of content for the user
        this includes mails and calendar items """
        total_count = 0
        for folder in self.account.root.walk():
            if folder.total_count > 0:
                print(str(folder) + ': ' + str(folder.total_count))
            total_count += folder.total_count
        return total_count

    def export_attachments(self, item):
        """ Export all attachments to the user folder """
        print(item.datetime_created)
        i = 0
        for attachment in item.attachments:
            i += 1
            if isinstance(attachment, FileAttachment):
                name = (str(item.datetime_created) + '_' +
                        attachment.name.replace('/', '_'))
                path = os.path.join(self.folder, name)
                with open(path, 'wb') as f:
                    f.write(attachment.content)
            elif isinstance(attachment, ItemAttachment):
                name = (str(item.datetime_created) + '_' +
                        attachment.name.replace('/', '_'))
                path = os.path.join(self.folder, name + '.txt')
                with open(path, 'w') as f:
                    print(type(attachment.item))
                    print(type(attachment))
                    print(attachment.item.subject)
                    print(attachment.item.body)
                    if attachment.item.name:
                        f.write(attachment.item.name)
                    if attachment.item.subject:
                        f.write(attachment.item.subject)
                    if attachment.item.body:
                        f.write(attachment.item.body)
            else:
                print(dir(attachment))
                print(type(attachment))
                raise(Exception('Unknown attachment'))
        assert(i == len(item.attachments))
        return len(item.attachments)

    def check_mail(self):
        attachments = 0
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)
        for folder in self.account.root.walk():
            print(folder)
            print(str(folder).find('VoiceMessages'))
            if folder.total_count == 0:
                continue
            for item in folder.all():
                attachments += self.export_attachments(item)
        print(attachments)
        print(len(os.listdir(self.folder)))
        assert(attachments == len(os.listdir(self.folder)))


if __name__ == '__main__':
    users = ['robj', 'brloe', 'clma', 'flho', 'henk', 'jewu', 'leim', 'mska',
             'yela', 'miah', 'oene', 'paha', 'pasp', 'pala', 'pira', 'tikh',
             'tomo']

    user = sys.argv[1]
    if user in users:
        scanner = ExchangeScan(user)
        print(scanner.total_mails())
        print(scanner.check_mail())

    """
            elif isinstance(attachment, CalendarIem):
                name = (str(item.datetime_created) + '_' +
                        attachment.uid.replace('/', '_'))
                path = os.path.join(self.folder, name + '.txt')
                with open(path, 'w') as f:
                    f.write(attachment.item.subject)
                    f.write(attachment.item.body)
            elif isinstance(attachment, Contact):
                name = (str(item.datetime_created) + '_' +
                        attachment.display_name.replace('/', '_'))
                path = os.path.join(self.folder, name + '.txt')
                with open(path, 'w') as f:
                    f.write(attachment.item.subject)
                    f.write(attachment.item.body)

    for user in users:
        print(user)
        scanner = ExchangeScan(user)
        print(scanner.total_mails())
        print(scanner.check_mail())
    """
