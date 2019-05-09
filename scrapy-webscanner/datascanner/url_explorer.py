#!/bin/sh

import argparse

from .model.core import Source, SourceManager
from .model.core import UnknownSchemeError

def print_source(manager, source, depth=0, guess=False):
    for h in source.handles(manager):
        print("{0}{1}".format("  " * depth, h))
        derived_source = Source.from_handle(h, manager if not guess else None)
        if derived_source:
            with SourceManager(manager) as derived_manager:
                print_source(derived_manager, derived_source, depth + 1, guess)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
            "urls",
            metavar="URL", nargs='+')
    parser.add_argument(
            "--compute-mime",
            action='store_false', dest='guess')
    parser.add_argument(
            "--guess-mime",
            action='store_true', dest='guess', default=True)

    args = parser.parse_args()

    sources = []
    with SourceManager() as sm:
        for i in args.urls:
            try:
                s = Source.from_url(i)
                print_source(sm, s, guess=args.guess)
            except UnknownSchemeError:
                pass

if __name__ == '__main__':
    main()
