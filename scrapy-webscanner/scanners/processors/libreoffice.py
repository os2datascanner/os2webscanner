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
import random
import hashlib
from django.conf import settings

base_dir = settings.BASE_DIR
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
        super(Processor, self).__init__()
        self.home_dir = None
        self.instance = None
        self.instance_name = None

    def setup_queue_processing(self, pid, *args):
        """Setup the home directory as the first argument."""
        super(LibreOfficeProcessor, self).setup_queue_processing(
            pid, *args
        )
        self.instance_name = args[0]
        dummy_home = os.path.join(home_root_dir, self.instance_name)
        if not os.path.exists(dummy_home):
            os.makedirs(dummy_home)

        args = [
            "/usr/lib/libreoffice/program/soffice.bin",
            "-env:UserInstallation=file://{0}".format(dummy_home),
            "--accept=pipe,name=cnv_{0};urp".format(self.instance_name),
            "--headless", "--nologo", "--quickstart=no"
            ]
        self.instance = subprocess.Popen(args)
        assert self.instance.poll() is None, """\
couldn't create a LibreOffice process"""

    def teardown_queue_processing(self):
        if self.instance:
            self.instance.terminate()
            self.instance.wait()
            self.instance = None
        super(LibreOfficeProcessor, self).teardown_queue_processing()

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
            output_filter = "htm:HTML"

        if output_filter == "csv":
            # TODO: Input type to filter mapping?
            output_file = os.path.join(
                tmp_dir,
                os.path.basename(item.file_path).split(".")[0] + ".csv"
            )

            return_code = subprocess.call([
                project_dir + "/scrapy-webscanner/unoconv",
                "--pipe", "cnv_{0}".format(self.instance_name), "--no-launch",
                "--format", output_filter,
                "-e", 'FilterOptions="59,34,0,1"',
                "--output", output_file, "-vvv",
                item.file_path
            ])
        else:
            # HTML
            return_code = subprocess.call([
                project_dir + "/scrapy-webscanner/unoconv",
                "--pipe", "cnv_{0}".format(self.instance_name), "--no-launch",
                "--format", output_filter,
                "--output", tmp_dir, "-vvv",
                item.file_path
            ])

        return return_code == 0


Processor.register_processor(LibreOfficeProcessor.item_type,
                             LibreOfficeProcessor)
