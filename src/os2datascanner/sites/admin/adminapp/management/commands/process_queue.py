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

"""Program which processes the queue of the given type.

Pass extra arguments to the processor after the first argument.
"""

import os
import signal
import sys

import structlog

from django.core.management.base import BaseCommand

from os2datascanner.engine.scanners.processors.processor import Processor

from os2datascanner.engine.utils import prometheus_session


def sigterm_handler(sig, frm):
    sys.exit(1)

# process needs to listen on
# signal.SIGTERM in order to tear down ressources.
signal.signal(signal.SIGTERM, sigterm_handler)


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            'processor_type',
            type=str,
            choices=sorted(Processor.processors_by_type),
            help='The document type to listen for and process.',
        )
        parser.add_argument(
            'extra_args',
            nargs='*',
            help='Arguments to pass to the processor.',
        )

    def handle(self, processor_type, extra_args, **kwargs):
        queued_processor = Processor.processor_by_type(processor_type)

        logger = structlog.get_logger()

        with prometheus_session(str(os.getpid()), processor_type=processor_type):
            if queued_processor is not None:
                queued_processor.setup_queue_processing(os.getpid(), *extra_args)

            logger.info('processor_ready', extra_args=extra_args)
            try:
                queued_processor.process_queue()
            except KeyboardInterrupt:
                pass
            finally:
                logger.info('processor_done')

                queued_processor.teardown_queue_processing()
