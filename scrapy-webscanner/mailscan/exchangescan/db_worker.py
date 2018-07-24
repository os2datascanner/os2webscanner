from django.db import connections, transaction, IntegrityError, DatabaseError

from os2webscanner.models.scan_model import Scan
from os2webscanner.models.url_model import Url


def close_all_db_connections():
    connections.close_all()


def get_scan_by_id(scan_id):
    scan_object = None
    try:
        with transaction.atomic():
            scan_object = Scan.objects.get(pk=scan_id)
    except (DatabaseError, IntegrityError) as ex:
        print('Error occured while getting scan object with id {}'.format(scan_id))
        print('Error message {}'.format(ex))

    return scan_object


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
