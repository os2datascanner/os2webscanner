#!/usr/bin/env python3

from ..model.core import Source, SourceManager
from ..model.http import WebHandle
from ..model.dummy import DummySource

from subprocess import run

# WebSource and SecureWebSource don't implement crawlers yet, but we can
# simulate a crawler by creating a number of WebHandles manually and packing
# them into a DummySource, which does nothing other than spit out handles
universe = [
    ("http://www.example.com", "/index.html"),
    ("http://www.example.net", "/index.html"),
    ("http://www.example.org", "/index.html"),
    ("https://www.example.com", "/index.html"),
    ("https://www.example.net", "/index.html"),
    ("https://www.example.org", "/index.html"),
]
handles = \
    [WebHandle(Source.from_url(source), page) for source, page in universe]

with SourceManager() as sm:
    def handle_source(s):
        for handle in s.handles(sm):
            if handle.guess_type() == "text/html":
                with handle.follow(sm).make_path() as path:
                    print("{0} -> {1}".format(handle, path))
                    run(["cat", path])

    handle_source(DummySource(*handles))
