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
import os

from urllib.request import urlopen

from django.db import models
from model_utils.managers import InheritanceManager


class Version(models.Model):

    objects = InheritanceManager()

    """A representation of an actual URL on a domain with its MIME type."""

    location = models.ForeignKey('Location', null=False,
                                 verbose_name='Location',
                                 related_name='versions',
                                 on_delete=models.PROTECT)
    scan = models.ForeignKey('Scan', null=False, verbose_name='Scan',
                             related_name='versions',
                             on_delete=models.CASCADE)

    mime_type = models.CharField(max_length=256, verbose_name='Content type',
                                 null=True)

    def __str__(self):
        """Return the URL."""
        return self.scan.webscanner.path_for(self.location.url)

    @property
    def url(self):
        return self.location.url

    @property
    def tmp_dir(self):
        """The path to the temporary directory associated with this url."""
        return os.path.join(self.scan.scan_dir, 'url_item_%d' % (self.pk))

    @property
    def content(self):
        try:
            file = urlopen(self.url)
            return file.read()
        except Exception as e:
            return str(e)
