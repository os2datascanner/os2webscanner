#!/usr/bin/env python3

# This small model demonstration program opens a ZIP file embedded in this
# source code and prints each of the files contained inside it to standard
# output by feeding these files to cat(1). All of the temporary files created
# as part of this process are automatically cleaned up.

from model.zip import ZipSource
from model.core import Source, SourceManager
from model.data import DataSource
from model.file import FilesystemSource

from subprocess import run

data = "data:application/zip;base64,\
UEsDBAoAAAAAADJ+OU4AAAAAAAAAAAAAAAAHABwAZm9sZGVyL1VUCQADACJLXB8iS1x1eAsAAQTo\
AwAABOgDAABQSwMECgAAAAAAL345TuAJT2wLAAAACwAAABAAHABmb2xkZXIvZmlsZTIudHh0VVQJ\
AAP5IUtc+SFLXHV4CwABBOgDAAAE6AMAAFNvIGlzIHRoaXMKUEsDBAoAAAAAADJ+OU5xlNoWFwAA\
ABcAAAAQABwAZm9sZGVyL2ZpbGUzLnR4dFVUCQADACJLXAAiS1x1eAsAAQToAwAABOgDAABUaGlz\
LCB0aHJlZSwgaXMgYSB0ZXN0ClBLAwQKAAAAAAAtfjlOjC3A+g8AAAAPAAAAEAAcAGZvbGRlci9m\
aWxlMS50eHRVVAkAA/UhS1z1IUtcdXgLAAEE6AMAAAToAwAAVGhpcyBpcyBhIHRlc3QKUEsBAh4D\
CgAAAAAAMn45TgAAAAAAAAAAAAAAAAcAGAAAAAAAAAAQAO1BAAAAAGZvbGRlci9VVAUAAwAiS1x1\
eAsAAQToAwAABOgDAABQSwECHgMKAAAAAAAvfjlO4AlPbAsAAAALAAAAEAAYAAAAAAABAAAApIFB\
AAAAZm9sZGVyL2ZpbGUyLnR4dFVUBQAD+SFLXHV4CwABBOgDAAAE6AMAAFBLAQIeAwoAAAAAADJ+\
OU5xlNoWFwAAABcAAAAQABgAAAAAAAEAAACkgZYAAABmb2xkZXIvZmlsZTMudHh0VVQFAAMAIktc\
dXgLAAEE6AMAAAToAwAAUEsBAh4DCgAAAAAALX45TowtwPoPAAAADwAAABAAGAAAAAAAAQAAAKSB\
9wAAAGZvbGRlci9maWxlMS50eHRVVAUAA/UhS1x1eAsAAQToAwAABOgDAABQSwUGAAAAAAQABABP\
AQAAUAEAAAAA"

with SourceManager() as sm:
    def handle_source(s):
        for handle in s.handles(sm):
            sub_source = Source.from_handle(handle)
            if sub_source:
                handle_source(sub_source)
            elif handle.guess_type() == "text/plain":
                with handle.follow(sm) as path:
                    print("{0} -> {1}".format(handle, path))
                    run(["cat", path])

    handle_source(Source.from_url(data))
