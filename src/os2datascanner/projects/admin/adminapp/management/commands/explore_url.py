"""Performs URL exploration on one or more Sources."""

import os.path

import argparse
from django.core.management.base import BaseCommand

from os2datascanner.engine2.demo import url_explorer
from os2datascanner.engine2.model.core import (
        Source,
        SourceManager,
        UnknownSchemeError,
)


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        url_explorer.add_arguments(parser)

    def handle(self, **kwargs):
        urls = kwargs['urls']
        guess, summarise = kwargs['guess'], kwargs['summarise']
        with SourceManager() as sm:
            for i in urls:
                try:
                    s = Source.from_url(i)
                    url_explorer.print_source(
                            sm, s, guess=guess, summarise=summarise)
                except UnknownSchemeError:
                    pass
