from django.db import connections, transaction, IntegrityError, DatabaseError

from os2webscanner.models.scan_model import Scan
from os2webscanner.models.url_model import Url


class DBWorker(object):

    scan_object = None

    def get_scan_by_id(self, scan_id):
        if self.scan_object is None:
            try:
                with transaction.atomic():
                    self.scan_object = Scan.objects.get(pk=scan_id)
            except (DatabaseError, IntegrityError) as ex:
                print('Error occured while getting scan object with id {}'.format(scan_id))
                print('Error message {}'.format(ex))

        return self.scan_object


def close_all_db_connections():
    connections.close_all()


def store_url_object(url, mime_type, scan_object):
    url_object = None
    try:
        with transaction.atomic():
            url_object = Url(url=url, mime_type=mime_type,
                             scan=scan_object)
            url_object.save()
    except (DatabaseError, IntegrityError) as ex:
        print('Error occured while getting scan object with id {}'.format(scan_object.pk))
        print('Error message {}'.format(ex))

    return url_object
