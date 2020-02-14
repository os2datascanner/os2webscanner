"""Reads metadata from one or more files."""

import os.path

import argparse
from django.core.management.base import BaseCommand

from os2datascanner.utils.metadata import guess_responsible_party
from os2datascanner.engine2.model.core import SourceManager
from os2datascanner.engine2.model.file import FilesystemHandle

def valid_path(path):
    if os.path.exists(path):
        return path
    else:
        raise argparse.ArgumentTypeError(
                "'{0}': No such file or directory".format(path))


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            'FILE',
            type=valid_path,
            nargs='+',
            help='the path to a document to read metadata from',
        )

    def handle(self, **kwargs):
        with SourceManager() as sm:
            for path in kwargs['FILE']:
                guesses = guess_responsible_party(
                        FilesystemHandle.make_handle(path), sm)
                print("{0}: {1}".format(path, guesses))
