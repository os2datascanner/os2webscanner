"""Processors."""

from os2webscanner.models import ConversionQueueItem
from django.db import transaction, IntegrityError, DatabaseError
from django.utils import timezone
import time
import os
import mimetypes
import sys
import magic

base_dir = os.path.realpath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)), '..', '..', '..'
))
var_dir = os.path.join(base_dir, "var")


class Processor(object):

    """Represents a Processor which can process spider and queue items.

    Provides methods to process queue items for the current processor type.
    Provides a central place to register processors and contains utility
    methods for other processors.
    """

    magic = magic.Magic(mime=True)

    processors_by_type = {}
    processor_instances = {}

    documents_to_process = 10

    @classmethod
    def processor_by_type(cls, processor_type):
        """Return a Processor instance registered for the given type.

        The instance returned is always the same instance.
        """
        processor = cls.processor_instances.get(processor_type, None)
        if processor is None:
            processor_class = cls.processors_by_type.get(processor_type, None)
            if processor_class is None:
                return None
            processor = processor_class()
            cls.processor_instances[processor_type] = processor
        return processor

    @classmethod
    def var_dir(self):
        """Return the base data directory.

        Temporary files, as well as configuration files needed by
        processors should go somewhere under this directory.
        """
        return var_dir

    def handle_spider_item(self, data, url_object):
        """Process an item from a spider. Must be overridden.

        :type url_object: Url
        :param data: The textual or binary data to process.
        :param url_object: The Url object that the data was found at.
        """
        raise NotImplemented

    def handle_queue_item(self, item):
        """Process an item from a queue. Must be overridden.

        :type item: ConversionQueueItem
        :param item: The ConversionQueueItem to process.
        """
        raise NotImplemented

    def add_to_queue(self, data, url_object):
        """Add an item to the conversion queue.

        The data will be saved to a temporary file and added to the
        conversion queue for later processing.
        """
        # Write data to a temporary file
        # Get temporary directory
        tmp_dir = os.path.join(
            var_dir,
            'scan_%d' % (url_object.scan.pk),
            'url_item_%d' % (url_object.pk)
        )
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)
        file_name = os.path.basename(url_object.url)
        if file_name == '':
            file_name = url_object.pk + ".data"
        tmp_file_path = os.path.join(tmp_dir, file_name)
        f = open(tmp_file_path, 'w')
        f.write(data)
        f.close()

        # Create a conversion queue item
        new_item = ConversionQueueItem(
            file=tmp_file_path,
            type=self.mimetype_to_processor_type(url_object.mime_type),
            url=url_object,
            status=ConversionQueueItem.NEW,
        )
        new_item.save()
        return True

    def process_file(self, file_path, url):
        """Open the file associated with the item and process the file data.

        Calls self.process.
        """
        try:
            f = open(file_path, "r")
            self.process(f.read(), url)
            f.close()
        except IOError, e:
            print repr(e)
            return False
        return True

    def setup_queue_processing(self, *args):
        """Setup the queue processor with additional arguments."""
        raise NotImplementedError

    def process_queue(self):
        """Process items in the queue in an infinite loop.

        If there are no items to process, waits 1 second before trying
        to get the next queue item.
        """
        print "Starting processing queue items of type %s, pid %s" % (
            self.item_type, os.getpid()
        )
        sys.stdout.flush()
        executions = 0

        while executions < self.documents_to_process:
            item = self.get_next_queue_item()
            if item is None:
                time.sleep(1)
            else:
                result = self.handle_queue_item(item)
                executions = executions + 1
                if not result:
                    item.status = ConversionQueueItem.FAILED
                    item.save()
                else:
                    item.delete()
                print "%s (%s): %s" % (
                    item.file_path,
                    item.url.url,
                    "success" if result else "fail"
                )
                sys.stdout.flush()

    @transaction.atomic
    def get_next_queue_item(self):
        """Get the next item in the queue.

        Returns None if there is nothing in the queue.
        """
        result = None

        while result is None:
            try:
                with transaction.atomic():
                    # Get the first unprocessed item of the wanted type
                    result = ConversionQueueItem.objects.filter(
                        type=self.item_type,
                        status=ConversionQueueItem.NEW
                    ).select_for_update(nowait=True).order_by("pk")[0]

                    # Change status of the found item
                    result.status = ConversionQueueItem.PROCESSING
                    result.process_id = os.getpid()
                    result.process_start_time = timezone.now()
                    result.save()
            except (DatabaseError, IntegrityError) as e:
                # Database transaction failed, we just try again
                print "".join([
                    "Transaction failed while getting queue item of type ",
                    "'" + self.item_type + "'"
                ])
                result = None
            except IndexError:
                # Nothing in the queue, return None
                result = None
                break
        return result

    def convert_queue_item(self, item):
        """Convert a queue item and add converted files to the queue.

        Creates a temporary directory for the queue item and calls
        self.convert to run the actual conversion. After converting,
        adds all files produced in the conversion directory to the queue.
        """
        scan_id = item.url.scan.pk
        tmp_dir = os.path.join(
            var_dir,
            'scan_%d' % (scan_id),
            'queue_item_%d' % (item.pk)
        )
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)

        result = self.convert(item, tmp_dir)
        if os.path.exists(item.file_path):
            os.remove(item.file_path)

        self.add_processed_files(item, tmp_dir)
        return result

    def convert(self, item, tmp_dir):
        """Convert the item and output converted files in the temp dir.

        Must be implemented by classes which call convert_queue_item.
        It is expected that the conversion outputs converted files in the
        temporary directory.
        """
        raise NotImplemented

    def add_processed_files(self, item, tmp_dir):
        """Recursively add all files in the temp dir to the queue."""
        for root, dirnames, filenames in os.walk(tmp_dir):
            for fname in filenames:
                # TODO: How do we decide which types are supported?
                try:
                    # Guess the mime type from the file name
                    mime_type, encoding = mimetypes.guess_type(fname)
                    file_path = os.path.join(root, fname)
                    if mime_type is None:
                        # Guess the mime type from the file contents
                        mime_type = self.magic.from_file(file_path)
                    processor_type = Processor.mimetype_to_processor_type(
                        mime_type)
                    if processor_type is not None:
                        new_item = ConversionQueueItem(
                            file=file_path,
                            type=processor_type,
                            url=item.url,
                            status=ConversionQueueItem.NEW,
                        )
                        new_item.save()
                except ValueError:
                    continue

    @classmethod
    def register_processor(cls, processor_type, processor):
        """Register the processor class as processor for the given type."""
        cls.processors_by_type[processor_type] = processor

    opendocument = 'application/vnd.oasis.opendocument'
    officedocument = 'application/vnd.openxmlformats-officedocument'

    mimetypes_to_processors = {
        'text': 'text',
        'image': 'ocr',

        'text/html': 'html',
        'text/xml': 'html',
        'application/xhtml+xml': 'html',
        'application/xml': 'html',
        'application/vnd.google-earth.kml+xml': 'html',

        'application/javascript': 'text',
        'application/json': 'text',
        'application/csv': 'text',

        'application/zip': 'zip',

        'application/pdf': 'pdf',

        'application/rtf': 'libreoffice',
        'application/msword': 'libreoffice',
        opendocument + '.chart': 'libreoffice',
        opendocument + '.database': 'libreoffice',
        opendocument + '.formula': 'libreoffice',
        opendocument + '.graphics': 'libreoffice',
        opendocument + '.graphics-template': 'libreoffice',
        opendocument + '.image': 'libreoffice',
        opendocument + '.presentation': 'libreoffice',
        opendocument + '.presentation-template': 'libreoffice',
        opendocument + '.spreadsheet': 'libreoffice',
        opendocument + '.spreadsheet-template': 'libreoffice',
        opendocument + '.text': 'libreoffice',
        opendocument + '.text-master': 'libreoffice',
        opendocument + '.text-template': 'libreoffice',
        opendocument + '.text-web': 'libreoffice',
        officedocument + '.presentationml.presentation': 'libreoffice',
        officedocument + '.presentationml.slide': 'libreoffice',
        officedocument + '.presentationml.slideshow': 'libreoffice',
        officedocument + '.presentationml.template': 'libreoffice',
        officedocument + '.spreadsheetml.sheet': 'libreoffice',
        officedocument + '.spreadsheetml.template': 'libreoffice',
        officedocument + '.wordprocessingml.document': 'libreoffice',
        officedocument + '.wordprocessingml.template': 'libreoffice',
        'application/vnd.ms-excel': 'libreoffice',
        'application/vnd.ms-powerpoint': 'libreoffice',
    }

    @classmethod
    def mimetype_to_processor_type(cls, mime_type):
        """Get the type name of the processor which handles the mime-type."""
        if mime_type is None:
            return None
        processor = cls.mimetypes_to_processors.get(mime_type, None)
        if processor is None:
            processor = cls.mimetypes_to_processors.get(
                mime_type.split("/")[0], None
            )
        return processor
