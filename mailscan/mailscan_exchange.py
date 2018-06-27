import os
import sys
from exchangelib import FileAttachment, ItemAttachment
from exchangelib import IMPERSONATION, ServiceAccount, Account
from exchangelib import EWSDateTime, EWSTimeZone, EWSDate
import password


class ExchangeScan(object):
    """ Library to export a users mailbox from Exchange to a filesystem """
    def __init__(self, user):
        #credentials = Credentials(username="mailscan",
        #                          password=password.password)
        credentials = ServiceAccount(username="mailscan",
                                     password=password.password)
        username = user + "@vordingborg.dk"
        self.export_path = 'users/' + username
        self.account = Account(primary_smtp_address=username,
                               credentials=credentials, autodiscover=True,
                               access_type=IMPERSONATION)
        print('Init complete')

    def total_mails(self):
        """ Return the total amounts of content for the user
        this includes mails and calendar items """
        total_count = 0
        for folder in self.account.root.walk():
            total_count += folder.total_count
        return total_count

    def export_attachments(self, item):
        """ Export all attachments to the user folder """
        i = 0
        for attachment in item.attachments:
            i = i + 1
            if isinstance(attachment, FileAttachment):
                name = (str(item.datetime_created) + '_' +
                        attachment.name.replace('/', '_'))
                path = os.path.join(self.export_path, name)
                with open(path, 'wb') as f:
                    f.write(attachment.content)
            elif isinstance(attachment, ItemAttachment):
                try:
                    name = (str(item.datetime_created) + '_' +
                            attachment.name.replace('/', '_'))
                    path = os.path.join(self.export_path, name + '.txt')
                    with open(path, 'w') as f:
                        f.write(name)
                        if attachment.item.subject:
                            f.write(attachment.item.subject)
                        if attachment.item.body:
                            f.write(attachment.item.body)
                except AttributeError:
                    pass
            else:
                print(dir(attachment))
                print(type(attachment))
                raise(Exception('Unknown attachment'))
        assert(i == len(item.attachments))
        return len(item.attachments)

    def list_non_empty_folders(self):
        """ Returns a list of all non-empty folders
        :return: A python list with all folders"""
        folder_list = []
        for folder in self.account.root.walk():
            if folder.total_count > 0:
                folder_list.append(folder)
        return folder_list

    def export_folder(self, folder):
        attachments = 0
        if not os.path.exists(self.export_path):
            os.makedirs(self.export_path)
        #items = folder.all()
        import time
        t = time.time()
        #items = folder.all().order_by('datetime_created').filter('datetime_created' < '2010-01-01')
        tz = EWSTimeZone.localzone()
        start_dt = tz.localize(EWSDateTime(2016, 1, 1, 0, 0))
        end_dt = tz.localize(EWSDateTime(2017, 1, 1, 0, 0))
        items = folder.all().filter(datetime_received__range=(start_dt, end_dt))
        print(time.time() - t)
        print('Exporting {} items'.format(len(items)))
        print(time.time() - t)
        i = 0
        for item in items:
            i = i + 1
            print(i)
            attachments += self.export_attachments(item)
        return attachments
    
    def check_mail(self, total_count=None):
        attachments = 0
        total_scanned = 0
        if not os.path.exists(self.export_path):
            os.makedirs(self.export_path)
        folders = self.list_non_empty_folders()
        for folder in folders:
            attachments += self.export_folder(folder)
            total_scanned += folder.total_count
            print("{} / {}".format(total_scanned, total_count))
        print(attachments)
        print(len(os.listdir(self.export_path)))
        assert(attachments == len(os.listdir(self.export_path)))


if __name__ == '__main__':
    users = ['robj', 'brloe', 'clma', 'flho', 'henk', 'jewu', 'leim', 'mska',
             'yela', 'miah', 'oene', 'paha', 'pasp', 'pala', 'pira', 'tikh',
             'tomo']

    #import pdb; pdb.set_trace()
    user = sys.argv[1]
    if user in users:
        scanner = ExchangeScan(user)
        total_count = scanner.total_mails()
        print(scanner.check_mail(total_count))
    
    """
    user = sys.argv[1]
    if user in users:
        scanner = ExchangeScan(user)
        #total_count = scanner.total_mails()
        import cProfile, pstats, io
        pr = cProfile.Profile()
        pr.enable()
        folder_list = scanner.list_non_empty_folders()
        pr.disable()
        s = io.StringIO()
        sortby = 'cumulative'
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        print(s.getvalue())
        #print(scanner.check_mail(total_count))

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
