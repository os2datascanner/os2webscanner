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

from processor import Processor
import os
import os.path
import subprocess
import random
import hashlib
from django.conf import settings

base_dir = settings.BASE_DIR
var_dir = settings.VAR_DIR
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

    def setup_home_dir(self):
        """Make a random unique home directory for LibreOffice."""
        while True:
            self.instance_name = hashlib.md5(str(random.random())).hexdigest()
            home_dir = os.path.join(home_root_dir, self.instance_name)

            if not os.path.exists(home_dir):
                self.set_home_dir(home_dir)
                break

    def set_home_dir(self, home_dir):
        """Set the LibreOffice home directory to the given directory."""
        self.home_dir = home_dir
        self.env = os.environ.copy()
        self.env['HOME'] = self.home_dir
        if not os.path.exists(self.home_dir):
            os.makedirs(self.home_dir)

    def setup_queue_processing(self, pid, *args):
        """Setup the home directory as the first argument."""
        super(LibreOfficeProcessor, self).setup_queue_processing(
            pid, *args
        )
        self.set_home_dir(os.path.join(home_root_dir, args[0]))

    def handle_spider_item(self, data, url_object):
        """Add the item to the queue."""
        return self.add_to_queue(data, url_object)

    def handle_queue_item(self, item):
        """Convert the queue item."""
        return self.convert_queue_item(item)

    def convert(self, item, tmp_dir):
        """Convert the item."""
        if self.home_dir is None:
            self.setup_homedir()

        # TODO: Input type to filter mapping?
        return_code = subprocess.call([
                                          "libreoffice", "--headless",
                                          "--convert-to", "htm:HTML",
                                          item.file_path, "--outdir", tmp_dir
                                      ], env=self.env)
        return return_code == 0


Processor.register_processor(LibreOfficeProcessor.item_type,
                             LibreOfficeProcessor)
