import os
import os.path
import time
import logging
import random
import multiprocessing
from multiprocessing import Queue
from datetime import timedelta
from exchangelib import FileAttachment, ItemAttachment
from exchangelib import IMPERSONATION, ServiceAccount, Account
from exchangelib import EWSDateTime, EWSTimeZone
from exchangelib.util import chunkify
from exchangelib.errors import ErrorInternalServerTransientError
from exchangelib.errors import ErrorCannotOpenFileAttachment
from exchangelib.errors import ErrorInternalServerError
from exchangelib.errors import ErrorInvalidOperation
from exchangelib.errors import ErrorTimeoutExpired
import password

logging.basicConfig(level=logging.ERROR)


class ExchangeMailboxScan(object):
    """ Library to export a users mailbox from Exchange to a filesystem """
    def __init__(self, user, start_date=None):
        credentials = ServiceAccount(username="mailscan",
                                     password=password.password)
        username = user + "@vordingborg.dk"
        self.export_path = 'users/' + username
        self.account = Account(primary_smtp_address=username,
                               credentials=credentials, autodiscover=True,
                               access_type=IMPERSONATION)
        self.start_date = start_date
        self.account.root.refresh()
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
            if attachment.name is None:
                # If we have no name, we assume that we no real atachment
                i = len(item.attachments)  # Make end-assertion happy
                continue
            if isinstance(attachment, FileAttachment):
                i = i + 1
                name = (str(item.datetime_created) + '_' +
                        str(random.random()) + '_' +
                        attachment.name.replace('/', '_')[-60:])
                path = os.path.join(self.export_path, name)
                try:
                    with open(path, 'wb') as f:
                        f.write(attachment.content)
                except TypeError:
                    pass  # Happens with empty attachments, consider logging
                except ErrorCannotOpenFileAttachment:
                    pass # Do now know what triggers this
            elif isinstance(attachment, ItemAttachment):
                i = i + 1
                try:
                    # Pick last 60 chars of name to prevens too-long filenames
                    name = (str(item.datetime_created) + '_' +
                            str(random.random()) + '_' +
                            attachment.name.replace('/', '_')[-60:])
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

    def _export_folder_subset(self, folder, start_dt=None, end_dt=None):
        try:
            attachments = 0
            tz = EWSTimeZone.localzone()
            if start_dt is None:
                start_dt = tz.localize(EWSDateTime(1900, 1, 1, 0, 0))
            if end_dt is None:
                end_dt = tz.localize(EWSDateTime(2100, 1, 1, 0, 0))
            #items = folder.all().filter(datetime_received__range=(start_dt,
            #                                                      end_dt))
            items = folder.all()
            items = items.filter(datetime_received__range=(start_dt,
                                                           end_dt))
            for chunk in chunkify(items, 10):
                for item in chunk:
                    attachments += self.export_attachments(item)
        except ErrorInternalServerError:
            attachments = -1
            time.sleep(10)
            print('ErrorInternalServerError')            
        except ErrorInvalidOperation:
            attachments = -1
            time.sleep(10)
            print('ErrorInvalidOperation')
        except ErrorTimeoutExpired:
            attachments = -1
            time.sleep(10)
            print('ErrorTimeoutExpired')
        except ErrorInternalServerTransientError:
            attachments = -1
            time.sleep(10)
            print('ErrorInternalServerTransientError')
        return attachments

    def _attempt_export(self, folder, start_dt=None, end_dt=None):
        subset_attach = -1
        while subset_attach < 0:
            subset_attach = self._export_folder_subset(folder, start_dt,
                                                       end_dt)
        return subset_attach

    def export_folder(self, folder):
        # Todo: Export to filesystem folder with folder as name
        attachments = 0
        tz = EWSTimeZone.localzone()
        if folder.total_count < 100:
            start_dt = tz.localize(EWSDateTime(1900, 1, 1, 0, 0))
            end_dt = tz.localize(EWSDateTime(2100, 1, 1, 0, 0))
            attachments += self._attempt_export(folder)
        else:
            start_dt = tz.localize(EWSDateTime(2010, 1, 1, 0, 0))
            # First, export everything before 2010
            attachments += self._attempt_export(folder, end_dt=start_dt)
            for i in range(0, 50):
                end_dt = start_dt + timedelta(days=90)
                attachments += self._attempt_export(folder, start_dt=start_dt,
                                                    end_dt=end_dt)
                start_dt = end_dt
            # Finally, export everything later than ~2022
            attachments += self._attempt_export(folder, start_dt=end_dt)
        #TODO: Write 'Done' file in directory to document it is done
        return attachments

    def check_mailbox(self, total_count=None):
        # Todo: Clean up folder
        # Todo: Only scan from self.start_date
        attachments = 0
        total_scanned = 0
        if not os.path.exists(self.export_path):
            os.makedirs(self.export_path)
        folders = self.list_non_empty_folders()
        for folder in folders:
            print('{}: Exporting: {} ({} items)'.format(self.export_path,
                                                        folder,
                                                        folder.total_count))
            attachments += self.export_folder(folder)
            total_scanned += folder.total_count
            #  print("{}: {} / {}".format(self.export_path, total_scanned,
            #  total_count))
        #TODO: Write 'Done' file in directory to document it is done
        print(attachments)
        print(len(os.listdir(self.export_path)))
        #  assert(attachments == len(os.listdir(self.export_path)))


class ExchangeServerScan(multiprocessing.Process):
    def __init__(self, user_queue):
        multiprocessing.Process.__init__(self)
        self.user_queue = user_queue

    def run(self):
        while not self.user_queue.empty():
            try:
                user_name = self.user_queue.get()
                print('Scaning {}'.format(user_name))
                scanner = ExchangeMailboxScan(user_name)
                total_count = scanner.total_mails()
                scanner.check_mailbox(total_count)
                print('Done with {}'.format(user_name))
            except MemoryError:
                print('We had a memory-error from {}'.format(user_name))
                self.user_queue.put(user_name)


if __name__ == '__main__':
    users = ['robj', 'brloe', 'clma', 'flho', 'henk', 'jewu', 'leim', 'mska',
             'yela', 'miah', 'oene', 'paha', 'pasp', 'pala', 'pira', 'tikh',
             'tomo']

    user_queue = Queue()
    for user in users:
        user_queue.put(user)

    scanners = {}
    for i in range(0, 5):  # Number of threads
        scanners[i] = ExchangeServerScan(user_queue)
        scanners[i].start()

    while True:
        number_of_processes = multiprocessing.active_children()
        print('Active threads: {}'.format(len(number_of_processes)))
        time.sleep(10)
