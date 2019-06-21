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

from urllib.request import urlopen

from django.db import models


class Location(models.Model):
    """A representation of an actual URL on a domain with its MIME type."""

    class Meta:
        unique_together = (("url", "scanner"),)

    url = models.URLField(max_length=2048, verbose_name="URL")
    scanner = models.ForeignKey(
        "Scanner",
        null=False,
        verbose_name="Scan",
        related_name="files",
        on_delete=models.CASCADE,
    )

    def __str__(self):
        """Return the URL."""
        return self.url

    @property
    def content(self):
        try:
            file = urlopen(self.url)
            return file.read()
        except Exception as e:
            return str(e)
