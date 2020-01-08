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
# OS2datascanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (https://os2.eu/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( https://os2.eu/ )

import  argparse
from    django.core.management.base import BaseCommand

from    ...utils import hash_handle
from    ...models.documentreport_model import DocumentReport
from    .pipeline_collector import _restructure_and_save_result


class Command(BaseCommand):
    """Imports results into the report database."""
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            "INPUT_FILE",
            type=argparse.FileType("rt"),
            help="a JSON Lines file containing result messages to import into"
                    " the report database")

    def handle(self, *args, **options):
        with options["INPUT_FILE"] as fp:
            for line in fp:
                line = line.strip()
                if line:
                    _restructure_and_save_result(line.encode("utf-8"))
