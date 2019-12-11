#!/usr/bin/env python
# The contents of this file are subject to the Mozilla Public License
# Version 2.0 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
#    http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# OS2Webscanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (http://www.os2web.dk/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( http://www.os2web.dk/ )
from django.core.management.base import BaseCommand

from os2datascanner.utils.system_utilities import json_utf8_decode
from os2datascanner.utils.amqp_connection_manager import start_amqp, \
    set_callback, start_consuming, ack_message

from ...models.documentreport_model import DocumentReport


def consume_results(channel, method, properties, body):
    print('Message recieved {} :'.format(body))
    ack_message(method)
    body = json_utf8_decode(body)

    path = body['handle']['path']
    origin = body['origin'] # "metadata", "match" or "problem"
    # ["metadata": body1, "match": body2, ]

    report, created = DocumentReport.objects.get_or_create(path=path)
    tag = body['scan_tag']
    if created: #tag not in report.data:
        report.data[tag] = {}
        report.data[tag][origin] += body
        report.save()
    else:
        report.data = body
        report.save()


class Command(BaseCommand):
    """Command for starting a pipeline collector process."""
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            "--results",
            type=str,
            help="the name of the AMQP queue to which filtered result objects"
                 + " should be red",
            default="os2ds_results")

    def handle(self, results, *args, **options):

        # Start listning on matches queue
        start_amqp(results)
        set_callback(consume_results, results)
        start_consuming()
