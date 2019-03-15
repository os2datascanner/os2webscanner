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
"""Zip file processors."""
import zipfile

from .processor import Processor


class ZipProcessor(Processor):

    """A processor which can handle zip-compressed files using unzip."""

    item_type = "zip"

    def handle_spider_item(self, data, url_object):
        """Add the item to the queue."""
        return self.add_to_queue(data, url_object)

    def handle_queue_item(self, item):
        """Conver the queue item."""
        return self.convert_queue_item(item)

    def convert(self, item, tmp_dir):
        """Extract the item using unzip."""
        try:
            zip_item = zipfile.ZipFile(item.file_path)
            zip_item.extractall(tmp_dir)
            return True
        except (RuntimeError, KeyError) as re:
            print('Extracting zip file {} failed.'.format(item.file_path))
            print('Error message {}'.format(re))
            return False


Processor.register_processor(ZipProcessor.item_type, ZipProcessor)
