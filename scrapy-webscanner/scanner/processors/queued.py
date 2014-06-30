from os2webscanner.models import ConversionQueueItem
from django.db import transaction, IntegrityError
from datetime import datetime 
import time
import os
import mimetypes

class QueuedProcessor(object):
    def __init__(self, item_type):
        self.item_type = item_type

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

    def add_processed_files(self, from_dir):
        for root, dirnames, filenames in os.walk(tmp_dir):
            for fname in files:
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
