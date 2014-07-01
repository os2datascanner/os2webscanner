from os2webscanner.models import ConversionQueueItem
from django.db import transaction, IntegrityError
from datetime import datetime 
import time
import os
import mimetypes

base_dir = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), '..', '..', '..'
)
var_dir = os.path.join(base_dir, "var")

class QueuedProcessor(object):
    def __init__(self, item_type):
        self.item_type = item_type


    mimetypes_to_processors = {
        'text': 'text',
        'image': 'ocr',

        'text/html': 'html',
        'application/javascript': 'text',
        'application/pdf': 'pdf',
        'application/msword': 'libreoffice',
        'application/vnd.oasis.opendocument.chart': 'libreoffice',
        'application/vnd.oasis.opendocument.database': 'libreoffice',
        'application/vnd.oasis.opendocument.formula': 'libreoffice',
        'application/vnd.oasis.opendocument.graphics': 'libreoffice',
        'application/vnd.oasis.opendocument.graphics-template': 'libreoffice',
        'application/vnd.oasis.opendocument.image': 'libreoffice',
        'application/vnd.oasis.opendocument.presentation': 'libreoffice',
        'application/vnd.oasis.opendocument.presentation-template': 'libreoffice',
        'application/vnd.oasis.opendocument.spreadsheet': 'libreoffice',
        'application/vnd.oasis.opendocument.spreadsheet-template': 'libreoffice',
        'application/vnd.oasis.opendocument.text': 'libreoffice',
        'application/vnd.oasis.opendocument.text-master': 'libreoffice',
        'application/vnd.oasis.opendocument.text-template': 'libreoffice',
        'application/vnd.oasis.opendocument.text-web': 'libreoffice',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'libreoffice',
        'application/vnd.openxmlformats-officedocument.presentationml.slide': 'libreoffice',
        'application/vnd.openxmlformats-officedocument.presentationml.slideshow': 'libreoffice',
        'application/vnd.openxmlformats-officedocument.presentationml.template': 'libreoffice',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'libreoffice',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.template': 'libreoffice',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'libreoffice',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.template': 'libreoffice',
        'application/vnd.ms-excel': 'libreoffice',
        'application/vnd.ms-powerpoint': 'libreoffice',
    }

    @classmethod
    def mimetype_to_processor(cls, mime_type):
        processor = cls.mimetypes_to_processors.get(mime_type, None)
        if processor is None:
            processor = cls.mimetypes_to_processors.get(mime_type.split("/")[0], None)
        return processor

    @transaction.atomic
    def get_next_item(self):
        result = None

        while result is None:
            try:
                with transaction.atomic():
                    # Get the first unprocessed item of the wanted type
                    result = ConversionQueueItem.objects.filter(
                        type=self.item_type,
                        status = ConversionQueueItem.NEW
                    ).order_by("pk")[0]

                    # Change status of the found item
                    result.status = ConversionQueueItem.PROCESSING
                    result.process_id = os.getpid()
                    result.process_start_time = datetime.now()
                    result.save()
            except IntegrityError:
                # Database transaction failed, we just try again
                print "".join(
                    "Transaction failed while getting queue item of type ",
                    "'" + item_type + "'"
                )
                result = None
            except IndexError:
                # Nothing in the queue, return None
                result = None
                break
        return result

    def run(self):
        keep_running = True

        # TODO: Need a locking mechanism to ensure we're not running multiple
        # instances:
        #
        #if(os.path.exists(self.lock_file)):
        #    raise "Lockfile '" + self.lock_file + "' exists, will not run"
        #
        #f = open(self.lock_file, 'a').close();
        #f.write(os.getpid())
        #f.close()

        while keep_running:
            item = self.get_next_item()
            if item is None:
                print "Sleeping..."
                time.sleep(1)
            else:
                scan_id = item.url.scan.pk
                tmp_dir = os.path.join(
                    var_dir,
                    'scan_%d' % (scan_id),
                    'queue_item_%d' % (item.pk)
                )
                if not os.path.exists(tmp_dir):
                    os.makedirs(tmp_dir)

                # TODO: Input type to filter mapping?
                result = self.convert(item, tmp_dir)
                os.remove(item.file_path)
                if not result:
                    item.status = ConversionQueueItem.FAILED
                else:
                    item.status = ConversionQueueItem.SUCCEEDED
                    # TODO: Delete item instead of changing status
                item.save()
                self.add_processed_files(item, tmp_dir)

    def convert(self, item, tmp_dir):
        raise NotImplemented

    def add_processed_files(self, item, tmp_dir):
        for root, dirnames, filenames in os.walk(tmp_dir):
            for fname in filenames:
                # TODO: How do we decide which types are supported?
                try:
                    mimetype, encoding = mimetypes.guess_type(fname)
                    if mimetype == "text/html" or mimetype[0:6] == "image/":
                        new_item = ConversionQueueItem(
                            file = fname,
                            type = mimetype,
                            url = item.url,
                            status = ConversionQueueItem.NEW,
                        )
                        new_item.save()
                except ValueError:
                    continue
