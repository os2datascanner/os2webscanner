#!/bin/sh

import argparse

from ..model.core import Source, SourceManager
from ..model.core import UnknownSchemeError, ResourceUnavailableError

def format_d(depth, fmt, *args, **kwargs):
    return "{0}{1}".format("  " * depth, fmt.format(*args, **kwargs))

def print_source(manager, source, depth=0, guess=False, summarise=False):
    for handle in source.handles(manager):
        print(format_d(depth, "{0}", handle))
        if summarise:
            resource = handle.follow(manager)
            try:
                size = resource.get_size().value
                mime = resource.compute_type()
                lm = resource.get_last_modified().value
                print(format_d(depth + 1, "size {0} bytes", size))
                print(format_d(depth + 1, "type {0}", mime))
                print(format_d(depth + 1, "lmod {0}", lm))
            except ResourceUnavailableError as ex:
                print(format_d(depth + 1, "not available: {0}", ex.args[1:]))
        derived_source = Source.from_handle(
                handle, manager if not guess else None)
        if derived_source:
            with SourceManager(manager) as derived_manager:
                print_source(derived_manager,
                        derived_source, depth + 1, guess, summarise)


def add_arguments(parser):
    parser.add_argument(
            "urls",
            metavar="URL",
            help='A URL to be explored.',
            nargs='+')
    parser.add_argument(
            "--guess-mime",
            action='store_true',
            dest='guess',
            help='Compute the MIME type of each file' +
                    ' based on its filename. (default)',
            default=True)
    parser.add_argument(
            "--compute-mime",
            action='store_false',
            dest='guess',
            help='Compute the MIME type of each file based on its content.')
    parser.add_argument(
            "--summarise",
            action='store_true',
            dest='summarise',
            help='Print a brief summary of the content of each file.')

def main():
    parser = argparse.ArgumentParser()
    add_arguments(parser)

    args = parser.parse_args()

    with SourceManager() as sm:
        for i in args.urls:
            try:
                s = Source.from_url(i)
                print_source(sm, s, guess=args.guess, summarise=args.summarise)
            except UnknownSchemeError:
                pass

if __name__ == '__main__':
    main()
