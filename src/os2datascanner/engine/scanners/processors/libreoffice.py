# The contents of this file are subject to the Mozilla Public License
# Version 2.0 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
#    http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# OS2Webscanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (http://www.os2web.dk/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( http://www.os2web.dk/ )
"""LibreOffice related processors."""
import mimetypes

from .processor import Processor
import os
import os.path
import subprocess
import hashlib
import pathlib
import logging
from django.conf import settings

from time import sleep

var_dir = settings.VAR_DIR
project_dir = settings.PROJECT_DIR
lo_dir = os.path.join(var_dir, "libreoffice")
home_root_dir = os.path.join(lo_dir, "homedirs")


class LibreOfficeProcessor(Processor):

    """Represents a Processor for LibreOffice documents.

    Allows setting of the "home" directory for the libreoffice program,
    so that multiple libreoffice conversions can be run simultaneously.
    """

    item_type = "libreoffice"

    def __init__(self):
        """Initialize the processor, setting an empty home directory."""
        super().__init__()
        self.home_dir = None
        self.instance = None
        self.instance_name = None
        self.unoconv = None

    def _make_args(self, accept=True):
        assert self.instance_name
        dummy_home = os.path.join(home_root_dir, self.instance_name)
        return [
            "/usr/lib/libreoffice/program/soffice",
            "-env:UserInstallation=file://{0}".format(dummy_home),
            "--{1}accept=pipe,name=cnv_{0};urp".format(
                    self.instance_name, "" if accept else "un"),
            "--headless", "--invisible"
        ]

    def setup_queue_processing(self, pid, *args):
        """Setup the home directory as the first argument."""
        super().setup_queue_processing(
            pid, *args
        )
        self.instance_name = args[0]
        self.instance = subprocess.Popen(self._make_args(accept=True))
        assert self.instance.poll() is None, """\
couldn't create a LibreOffice process"""

    def teardown_queue_processing(self):
        logging.info('Tearing down libreoffice queue processor: {}'.format(
            self.instance_name)
        )
        try:
            if self.unoconv:
                logging.info('Terminating unoconv...')
                # If we were interrupted in the middle of trying to run
                # unoconv, then kill it off: a stuck unoconv instance might
                # remain attached to the pipe, corrupting messages sent by
                # future LibreOffice processors
                self.unoconv.terminate()
                try:
                    self.unoconv.wait(10)
                except subprocess.TimeoutExpired:
                    self.unoconv.kill()
                    self.unoconv.wait()
                finally:
                    self.unoconv = None
            if self.instance and self.instance.poll() is None:
                logging.info('Terminating instance...')
                # LibreOffice is still running; try to shut it down cleanly,
                # but do so messily if necessary

                # Try to convince the existing instance to stop listening on
                # the pipe (this subprocess will send that instruction and then
                # stop immediately)...
                terminator = subprocess.Popen(self._make_args(accept=False) +
                        ['--terminate_after_init'])
                try:
                    terminator.wait(10)
                except subprocess.TimeoutExpired:
                    # (... unless it, too, got stuck, in which case we kill it
                    # and keep going...)
                    terminator.kill()
                    terminator.wait()
                finally:
                    # ... and now kill the underlying LibreOffice process off
                    self.instance.terminate()
                    try:
                        self.instance.wait(10)
                    except subprocess.TimeoutExpired:
                        self.instance.kill()
                        self.instance.wait()
                    finally:
                        self.instance = None
        finally:
            self._unlink_home_socket()
            super().teardown_queue_processing()

    def _unlink_home_socket(self):
        """\
Remove the Unix domain socket used to control access to the LibreOffice home
folder."""
        # (Yes, this depends on a whole host of tiny implementation details,
        # but the alternative is to rewrite the whole processor to use
        # PyUNO...)
        dummy_home_uri = \
            (pathlib.Path(home_root_dir) / self.instance_name).as_uri()
        # LibreOffice represents (most of...) its strings as UTF-16 strings in
        # system byte order. (Remember to remove the BOM!)
        home_hash = hashlib.md5(dummy_home_uri.encode("UTF-16")[2:])
        # The string representation of the MD5 hash that LibreOffice generates
        # here is generated by snprintf'ing all of the bytes together using the
        # "%x" format specifier, which means the resulting "MD5 hash" might
        # have fewer than thirty-two characters(!!!) (No, really, the
        # source code even explicitly comments on this: see the get_md5hash
        # function in desktop/unx/source/start.c...)
        home_hash = "".join(["{:x}".format(c) for c in home_hash.digest()])
        lock_path = \
            pathlib.Path("/tmp/OSL_PIPE_{0}_SingleOfficeIPC_{1}".format(
                    os.getuid(), home_hash))
        if lock_path.is_socket():
            # This instance is not running; remove the socket
            lock_path.unlink()

    def handle_spider_item(self, data, url_object):
        """Add the item to the queue."""
        return self.add_to_queue(data, url_object)

    def handle_queue_item(self, item):
        """Convert the queue item."""
        return self.convert_queue_item(item)

    def convert(self, item, tmp_dir):
        """Convert the item."""
        # TODO: Use the mime-type detected by the scanner
        mime_type, encoding = mimetypes.guess_type(item.file_path)
        if not mime_type:
            mime_type = self.mime_magic.from_file(item.file_path)

        if (mime_type == "application/vnd.ms-excel"
                or "spreadsheet" in mime_type):
            # If it's a spreadsheet, we want to convert to a CSV file
            output_filter = "csv"
        else:
            # Default to converting to HTML
            output_filter = "html"

        if output_filter == "csv":
            # TODO: Input type to filter mapping?
            output_file = os.path.join(
                tmp_dir,
                os.path.basename(item.file_path).split(".")[0] + ".csv"
            )

            unoconv_args = [
                project_dir + "/bin/unoconv",
                "--pipe", "cnv_{0}".format(self.instance_name), "--no-launch",
                "--format", output_filter,
                "-e", 'FilterOptions="59,34,0,1"',
                "--output", output_file, "-vvv",
                item.file_path
            ]
        else:
            # HTML
            unoconv_args = [
                project_dir + "/bin/unoconv",
                "--pipe", "cnv_{0}".format(self.instance_name), "--no-launch",
                "--format", output_filter,
                "--output", tmp_dir + "/", "-vvv",
                item.file_path
            ]

        attempts = 0
        while attempts < 4:
            return_code = 113
            self.unoconv = subprocess.Popen(unoconv_args)
            return_code = self.unoconv.wait()
            self.unoconv = None
            # unoconv returns 113 if the connection failed; if that happens and
            # the instance is still running, then it's probably starting up, so
            # try a few more times over the course of a minute
            if return_code == 113 and self.instance.poll() is None:
                sleep(15)
                attempts += 1
            else:
                return return_code == 0
        return False


Processor.register_processor(LibreOfficeProcessor.item_type,
                             LibreOfficeProcessor)
