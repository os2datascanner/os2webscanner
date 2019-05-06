#!/usr/bin/env python3

# This small model demonstration program opens a ZIP file embedded in this
# source code and prints each of the plain text files contained inside it, one
# of which is itself inside another ZIP file, to standard output by feeding
# these files to cat(1). All of the temporary files created as part of this
# process are automatically cleaned up.

from .model.core import Source, SourceManager

from subprocess import run

data = "data:application/zip;base64,\
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"

with SourceManager() as sm:
    def handle_source(s):
        for handle in s.handles(sm):
            sub_source = Source.from_handle(handle, sm)
            if sub_source:
                handle_source(sub_source)
            elif handle.guess_type() == "text/plain":
                with handle.follow(sm).make_path() as path:
                    print("{0} -> {1}".format(handle, path))
                    run(["cat", path])

    handle_source(Source.from_url(data))
