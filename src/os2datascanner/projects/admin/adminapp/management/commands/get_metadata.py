"""Reads metadata from one or more files."""

import os.path

import argparse
from django.core.management.base import BaseCommand

from os2datascanner.utils.metadata import guess_responsible_party


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
        for path in kwargs['FILE']:
            print("{0}: {1}".format(path, guess_responsible_party(path)))
