import sys
import time
import shutil
import random
import logging
import subprocess
import multiprocessing
from pathlib import Path
from multiprocessing import Queue
from datetime import timedelta
from exchangelib import FileAttachment, ItemAttachment
from exchangelib import IMPERSONATION, ServiceAccount, Account
from exchangelib import EWSDateTime, EWSTimeZone
from exchangelib.util import chunkify
from exchangelib.errors import ErrorNonExistentMailbox
from exchangelib.errors import ErrorInternalServerTransientError
from exchangelib.errors import ErrorCannotOpenFileAttachment
from exchangelib.errors import ErrorInternalServerError
from exchangelib.errors import ErrorInvalidOperation
from exchangelib.errors import ErrorTimeoutExpired
import password

exchangelogger = logging.getLogger('exchangelib')
exchangelogger.setLevel(logging.ERROR)

logger = logging.Logger('Mailscan_exchange')
fh = logging.FileHandler('logfile.log')
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)

class ExportError(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)

class ExchangeMailboxScan(object):
    """ Library to export a users mailbox from Exchange to a filesystem """
    def __init__(self, user, start_date=None):
        credentials = ServiceAccount(username="mailscan",
                                     password=password.password)
        username = user + "@vordingborg.dk"
        self.export_path = Path('/mnt/new_var/mailscan/users/' + username)
        self.current_path = None
        self.start_date = start_date
        try:
            self.account = Account(primary_smtp_address=username,
                                   credentials=credentials, autodiscover=True,
                                   access_type=IMPERSONATION)
            self.account.root.refresh()
            logger.info('{}: Init complete'.format(username))
        except ErrorNonExistentMailbox:
            logger.error('No such user: {}'.format(username))
            self.account = None

    def total_mails(self):
        """ Return the total amounts of content for the user
        this includes mails and calendar items """
        if self.account is None: # This could be a decorator
            return False
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
                path = self.current_path.joinpath(name)
                try:
                    with path.open('wb') as f:
                        f.write(attachment.content)
                except TypeError:
                    pass  # Happens with empty attachments, consider logging
                except ErrorCannotOpenFileAttachment:
                    pass # Do now know what triggers this?
            elif isinstance(attachment, ItemAttachment):
                i = i + 1
                try:
                    # Pick last 60 chars of name to prevens too-long filenames
                    name = (str(item.datetime_created) + '_' +
                            str(random.random()) + '_' +
                            attachment.name.replace('/', '_')[-60:])
                    path = self.current_path.joinpath(name + '.txt')
                    with path.open('w') as f:
                        f.write(name)
                        if attachment.item.subject:
                            f.write(attachment.item.subject)
                        if attachment.item.body:
                            f.write(attachment.item.body)
                except AttributeError:
                    pass
            else:
                raise(Exception('Unknown attachment'))
        assert(i == len(item.attachments))
        return len(item.attachments)

    def list_non_empty_folders(self):
        """ Returns a list of all non-empty folders
        :return: A python list with all folders"""
        if self.account is None: # This could be a decorator
            return False
        folder_list = []
        for folder in self.account.root.walk():
            if folder.total_count > 0:
                folder_list.append(folder)
        return folder_list

    def _export_folder_subset(self, folder, start_dt=None, end_dt=None):
        # Todo: Consider whether we need caching on date-level
        try:
            attachments = 0
            tz = EWSTimeZone.localzone()
            if start_dt is None:
                start_dt = tz.localize(EWSDateTime(1900, 1, 1, 0, 0))
            if end_dt is None:
                end_dt = tz.localize(EWSDateTime(2100, 1, 1, 0, 0))
            items = folder.all()
            items = items.filter(datetime_received__range=(start_dt,
                                                           end_dt))
            for chunk in chunkify(items, 10):
                for item in chunk:
                    attachments += self.export_attachments(item)
        except ErrorInternalServerError:
            attachments = -1
            time.sleep(300)
            logger.warning('{}: ErrorInternalServerError'.format(self.export_path))            
        except ErrorInvalidOperation:
            attachments = -1
            time.sleep(300)
            logger.warning('{}: ErrorInvalidOperation'.format(self.export_path))
        except ErrorTimeoutExpired:
            attachments = -1
            time.sleep(300)
            logger.warning('{}: ErrorTimeoutExpired'.format(self.export_path))
        except ErrorInternalServerTransientError:
            attachments = -1
            time.sleep(60)
            warning = '{}, {}: ErrorInternalServerTransientError'
            logger.warning(warning.format(self.export_path, folder))
        return attachments

    def _attempt_export(self, folder, start_dt=None, end_dt=None):
        subset_attach = -1
        attempts = 0
        while subset_attach < 0 and attempts < 5:
            attempts += 1
            subset_attach = self._export_folder_subset(folder, start_dt,
                                                       end_dt)
        if subset_attach == -1:
            raise ExportError('Unable to export folder')
        return subset_attach

    def export_folder(self, folder):
        folder_name = folder.name.replace(' ', '_').replace('/', '_')
        self.current_path = self.export_path.joinpath(folder_name)
        if self.export_path.joinpath(folder.name + '_done').exists():
            # print('Aleady done: {}'.format(self.current_path))
            return 0 # Already scanned
        if self.current_path.exists():
            print('Clean up: {}'.format(self.current_path))
            shutil.rmtree(str(self.current_path))
        self.current_path.mkdir()

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
        self.current_path.rename(str(self.current_path) + '_done')
        return attachments

    def check_mailbox(self, total_count=None, clear_mailbox=False):
        # Todo: Clean up folder
        # Todo: Only scan from self.start_date
        if self.account is None:
            return False
        attachments = 0
        total_scanned = 0
        if not self.export_path.exists():
            self.export_path.mkdir()
        folders = self.list_non_empty_folders()
        for folder in folders:
            info_string = '{}: Exporting: {} ({} items)'
            logger.info(info_string.format(self.export_path,
                                           folder,
                                           folder.total_count))
            attachments += self.export_folder(folder)
            total_scanned += folder.total_count
            logger.info("Exported {}: {} / {}".format(self.export_path,
                                                      total_scanned,
                                                      total_count))
        return True


class ExchangeServerScan(multiprocessing.Process):
    def __init__(self, user_queue):
        multiprocessing.Process.__init__(self)
        self.user_queue = user_queue

    def run(self):
        while not self.user_queue.empty():
            try:
                user_name = self.user_queue.get()
                logger.info('Scaning {}'.format(user_name))
                scanner = ExchangeMailboxScan(user_name)
                total_count = scanner.total_mails()
                scanner.check_mailbox(total_count)
                logger.info('Done with {}'.format(user_name))
            except MemoryError:
                logger.error('We had a memory-error from {}'.format(user_name))
                self.user_queue.put(user_name)
            except ExportError:
                logger.error('Could not export all of {}'.format(user_name))
                self.user_queue.put(user_name)


if __name__ == '__main__':
    users = ['robj', 'brloe', 'clma', 'flho', 'henk', 'jewu', 'leim', 'mska',
             'yela', 'miah', 'oene', 'paha', 'pasp', 'pala', 'pira', 'tikh',
             'tomo']

    user_path = Path('./user.txt')
    with user_path.open('r') as f:
        users = f.read().split('\n')
    for user in users:
        if len(user.strip()) == 0:
            users.remove(user)

    number_of_threads = int(sys.argv[1])
    
    user_queue = Queue()
    for user in users:
        user_queue.put(user)

    scanners = {}
    for i in range(0, number_of_threads):
        scanners[i] = ExchangeServerScan(user_queue)
        scanners[i].start()

    start_time = time.time()
    status = 'Threads: {}. Queue: {}. Export: {:.3f}GB. Time: {:.2f}'
    while True:
        processes = multiprocessing.active_children()
        du_output = subprocess.check_output(['du', '-s',
                                             '/mnt/new_var/mailscan/users/'])
        export_size = float(du_output.decode('utf-8').split('\t')[0])
        print(status.format(len(processes),
                           user_queue.qsize(),
                           export_size  / 1024**2,
                           (time.time() - start_time)/60.0)
        )
        time.sleep(20)
