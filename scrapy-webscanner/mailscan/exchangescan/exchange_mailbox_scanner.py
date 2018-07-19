"""
Design:
* Login with exchange user
* Load mail users from file
* Get domain
* Start download
* For everyfile ...
ideas:
 - start a scrapy crawler for every file or folder.
 - parse mail data directly to processer and put attachments in conversionqueue.
"""
import logging
from .utils import init_logger
import time

from datetime import timedelta

from exchangelib import EWSDateTime, EWSDate, UTC
from exchangelib import FileAttachment, ItemAttachment
from exchangelib import IMPERSONATION, ServiceAccount, Account
from exchangelib.util import chunkify
from exchangelib.errors import ErrorNonExistentMailbox
from exchangelib.errors import ErrorInternalServerTransientError
from exchangelib.errors import ErrorCannotOpenFileAttachment
from exchangelib.errors import ErrorInternalServerError
from exchangelib.errors import ErrorInvalidOperation
from exchangelib.errors import ErrorTimeoutExpired

from os2webscanner.models.url_model import Url

exchangelogger = logging.getLogger('exchangelib')
exchangelogger.setLevel(logging.DEBUG)

logger = logging.Logger('Echange_mailbox_scanner')
# logger.setLevel(logging.DEBUG)


class ExportError(Exception):
    """ Exception to indicate that export failed for unspecified reasons """
    def __init__(self, *args, **kwargs):
        logger.error('Export Exception')
        Exception.__init__(self, *args, **kwargs)


class ExchangeMailboxScanner(object):
    """ Library to export a users mailbox from Exchange to a filesystem """
    def __init__(self, user, domain, exchange_scanner):
        self.logger = init_logger(self.__name__,
                                        exchange_scanner,
                                        logging.DEBUG)
        self.exchange_scanner = exchange_scanner
        username = domain.authentication.username
        self.logger.debug('Username: {}'.format(username))
        password = domain.authentication.get_password()
        credentials = ServiceAccount(username=username,
                                     password=password)
        smtp_address = user + domain.url
        self.logger.debug('Email address: {}'.format(smtp_address))
        self.current_path = None
        try:
            self.account = Account(primary_smtp_address=smtp_address,
                                   credentials=credentials,
                                   autodiscover=True,
                                   access_type=IMPERSONATION)
            self.account.root.refresh()
            self.logger.info('{}: Init complete'.format(smtp_address))
        except ErrorNonExistentMailbox:
            self.logger.error('No such user: {}'.format(smtp_address))
            self.account = None

    def total_mails(self):
        """ Return the total amounts of content for the user
        this includes mails and calendar items """
        total_count = 0
        if self.account is not None:
            for folder in self.account.root.walk():
                total_count += folder.total_count
        return total_count

    def export_item_body(self, item):
        """ Export the actual message body to a text processor
        :param item: The exchange item to be exported
        :return: List of inline attachments that should be ignored
        """
        subject = item.subject
        if subject is None:
            subject = ''

        msg_body = str(item.body)

        url_object = Url(url=subject, mime_type='utf-8',
                         scan=self.scanner.scan_object)
        url_object.save()

        data_to_scan = '{} {}'.format(subject, msg_body)
        self.exchange_scanner.scanner.scan(data_to_scan,
                                           url_object)

        # Make a list inline images, mostly used for logos in footers:
        footer_images = []
        cid_pos = 0
        end_pos = 0
        while cid_pos > -1:
            cid_pos = msg_body.find('cid:', end_pos)
            if cid_pos > 0:
                end_pos = msg_body.find('"', cid_pos)
                cid_string = msg_body[cid_pos:end_pos]
                # Format for cid-string: cid:image001.jpg@01D1189A.A75327D0
                img_name = cid_string[4:cid_string.find('@')]
                footer_images.append(img_name)
        return footer_images

    def export_attachments(self, item, skip_list):
        """ Export all attachments to the users folder
        :param item: The exchange item to export attachments from
        :skip_list: List of attachments that should not be exported
        :return: Number of attachments in item (including skipped...)
        """
        i = 0
        for attachment in item.attachments:
            if attachment.name is None:
                # If we have no name, we assume that we no real atachment
                i += 1  # Make end-assertion happy
                continue
            if attachment.name in skip_list:
                self.logger.debug('Skippig {}: '.format(attachment.name))
                i += 1  # Make end-assertion happy
                continue
            if isinstance(attachment, FileAttachment):
                i = i + 1
                url_object = Url(url=attachment.name,
                                 mime_type=attachment.conten_type,
                                 scan=self.scanner.scan_object)
                url_object.save()
                try:
                    self.exchange_scanner.scanner.scan(attachment.content,
                                                       url_object)
                except TypeError:
                    self.logger.error('Type Error')  # Happens for empty attachments
                except ErrorCannotOpenFileAttachment:
                    # Not sure when this happens
                    msg = 'ErrorCannotOpenFileAttachment {}'
                    self.logger.error(msg.format(self.current_path))
            elif isinstance(attachment, ItemAttachment):
                i = i + 1
                try:
                    subject = attachment.item.subject
                    if subject:
                        url_object = Url(url=subject,
                                         mime_type='utf-8',
                                         scan=self.scanner.scan_object)
                        url_object.save()
                    else:
                        url_object = Url(url=attachment.item.last_modified_time,
                                         mime_type='utf-8',
                                         scan=self.scanner.scan_object)
                        url_object.save()
                    data_to_scan = '{} {}'.format(subject, attachment.item.body)
                    self.exchange_scanner.scanner.scan(data_to_scan,
                                                       url_object)
                except AttributeError:
                    msg = 'AttributeError {}'
                    self.logger.error(msg.format(self.current_path))

            else:
                raise(Exception('Unknown attachment'))
        assert(i == len(item.attachments))
        return len(item.attachments)

    def list_non_empty_folders(self):
        """ Returns a list of all non-empty folders
        :return: A python list with all folders"""
        folder_list = []
        if self.account is not None:
            for folder in self.account.root.walk():
                if folder.total_count > 0:
                    folder_list.append(folder)
        return folder_list

    def _export_folder_subset(self, folder, start_dt=None, end_dt=None):
        """ Export a time-subset of an exchange folder
        :param folder: The exchange folder to export
        :start_dt: The start date to export from, default 1900-01-01
        :end_dt: The end date to export to, default 2100-01-01
        :return: Number of attachments in folder
        """
        try:
            attachments = 0
            if start_dt is None:
                start_dt = EWSDate(1900, 1, 1)
            if end_dt is None:
                end_dt = EWSDate(2100, 1, 1)
            items = folder.all()
            start_dt = UTC.localize(EWSDateTime(start_dt.year, start_dt.month,
                                                start_dt.day, 0, 0))
            end_dt = UTC.localize(EWSDateTime(end_dt.year, end_dt.month,
                                              end_dt.day, 0, 0))
            items = items.filter(datetime_received__range=(start_dt, end_dt))
            for chunk in chunkify(items, 10):
                for item in chunk:
                    skip_list = self.export_item_body(item)
                    attachments += self.export_attachments(item, skip_list)

        except ErrorInternalServerError:
            # Possibly happens on p7m files?
            msg = '{}: ErrorInternalServerError, giving up sub-folder'
            msg += ' Attachment value: {}'
            self.logger.warning(msg.format(self.export_path, attachments))
        except ErrorInvalidOperation:
            msg = '{}: ErrorInvalidOperation, giving up sub-folder'
            msg += ' Attachment value: {}'
            self.logger.warning(msg.format(self.export_path, attachments))
        except ErrorTimeoutExpired:
            attachments = -1
            time.sleep(30)
            self.logger.warning('{}: ErrorTimeoutExpired'.format(self.export_path))
        except ErrorInternalServerTransientError:
            attachments = -1
            time.sleep(30)
            warning = '{}, {}: ErrorInternalServerTransientError'
            self.logger.warning(warning.format(self.export_path, folder))
        return attachments

    def _attempt_export(self, folder, start_dt=None, end_dt=None):
        """ Attempt to export a folder, will re-try a number of time
        to increase tolerance to temporary errors on the server
        :param folder: The folder to scan
        :param start_dt: The start time of the export
        :param end_dt: The end time of the export
        :return: Number of exported attachments
        """
        self.logger.debug('Export {} from {} to {}'.format(self.current_path,
                                                           start_dt,
                                                           end_dt))
        subset_attach = -1
        attempts = 0
        while subset_attach < 0 and attempts < 5:
            attempts += 1
            subset_attach = self._export_folder_subset(folder,
                                                       start_dt,
                                                       end_dt)
        if subset_attach == -1:
            raise ExportError('Unable to export folder')
        return subset_attach

    def export_folder(self, folder):
        """ Export a given folder
        :param folder: The folder to export
        :return: The number of exported attachments
        """
        attachments = 0
        if self.start_date is None:
            start_dt = EWSDate(2010, 1, 1)
            # First, export everything before 2010
            attachments += self._attempt_export(folder, end_dt=start_dt)
        else:
            start_dt = self.start_date
            end_dt = start_dt + timedelta(days=10)
            while end_dt < EWSDate(2022, 1, 1):
                attachments += self._attempt_export(folder, start_dt=start_dt,
                                                    end_dt=end_dt)
                start_dt = end_dt
                end_dt = start_dt + timedelta(days=10)
            # Finally, export everything later than 2022
            attachments += self._attempt_export(folder, start_dt=end_dt)
        try:
            self.current_path.rename(str(self.current_path) + '_done')
        except FileNotFoundError:
            # This can happen if a user mistakenly is scanned twice at
            # the same time
            # For now we will log and do no more. The offending folder
            # will still contain the export, but will lose the information
            # that it is already scanned and thus will be re-scanned on
            # next run.
            self.logger.error('Rename error from {}'.format(self.current_path))
        return attachments

    def check_mailbox(self, total_count=None):
        """ Run an export of the mailbox
        :param total_count: The total amount of mail for progress report
        :param start_dt: Only export from this time.
        :return: Returns true if the account exists
        """
        if self.account is None:
            return False
        attachments = 0
        total_scanned = 0

        folders = self.list_non_empty_folders()
        for folder in folders:
            info_string = 'Exporting: {} ({} items)'
            self.logger.info(info_string.format(folder,
                                                folder.total_count))
            attachments += self.export_folder(folder)
            total_scanned += folder.total_count
            self.logger.info("Exported: {} / {}".format(total_scanned,
                                                        total_count))
        return True



