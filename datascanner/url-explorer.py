#!/bin/sh

import sys

from model.core import Source, SourceManager
from model.core import UnknownSchemeError

def print_source(manager, source, depth=0):
  for h in source.handles(manager):
    print("{0}{1}".format("  " * depth, h))
    derived_source = Source.from_handle(h)
    if derived_source:
      print_source(manager, derived_source, depth + 1)

if __name__ == '__main__':
  sources = []
  for i in sys.argv:
    try:
      s = Source.from_url(i)
      print(s)
      sources.append(s)
    except UnknownSchemeError:
      pass
  with SourceManager() as sm:
    for s in sources:
      print_source(sm, s)
