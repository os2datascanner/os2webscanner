#!/bin/sh

from sys import stderr
import argparse

from ..model.core import Source, SourceManager
from ..model.core import FileResource
from ..model.core import UnknownSchemeError, ResourceUnavailableError

def format_d(depth, fmt, *args, **kwargs):
    return "{0}{1}".format("  " * depth, fmt.format(*args, **kwargs))

def print_source(manager, source, depth=0, *,
        guess=False, summarise=False, max_depth=None):
    for handle in source.handles(manager):
        print(format_d(depth, "{0}", handle))
        if summarise:
            resource = handle.follow(manager)
            try:
                if isinstance(resource, FileResource):
                    size = resource.get_size().value
                    mime = resource.compute_type()
                    lm = resource.get_last_modified().value
                    print(format_d(depth + 1, "size {0} bytes", size))
                    print(format_d(depth + 1, "type {0}", mime))
                    print(format_d(depth + 1, "lmod {0}", lm))
            except ResourceUnavailableError as ex:
                print(format_d(depth + 1, "not available: {0}", ex.args[1:]))
        if max_depth is None or depth < max_depth:
            derived_source = Source.from_handle(
                    handle, manager if not guess else None)
            if derived_source:
                print_source(manager, derived_source, depth + 1,
                        guess=guess, summarise=summarise, max_depth=max_depth)


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
    parser.add_argument(
            "--max-depth",
            metavar="DEPTH",
            type=int,
            help="Don't recurse deeper than %(metavar)s levels.")

def main():
    parser = argparse.ArgumentParser()
    add_arguments(parser)

    args = parser.parse_args()

    with SourceManager() as sm:
        for i in args.urls:
            try:
                s = Source.from_url(i)
                if not s:
                    print("{0}: URL parsing failure".format(i), file=stderr)
                else:
                    print_source(sm, s,
                            guess=args.guess,
                            summarise=args.summarise,
                            max_depth=args.max_depth)
            except UnknownSchemeError as ex:
                print("{0}: unknown URL scheme".format(i), file=stderr)

if __name__ == '__main__':
    main()
