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

import re

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from .alias_model import Alias


_sid = re.compile("^S-1-\d+(-\d+){0,15}$")

def validate_sid(value):
    if not _sid.match(value):
        raise ValidationError(
                _("%(value)s is not a valid SID"),
                params={"value": value})


class ADSIDAlias(Alias):

    sid = models.CharField(max_length=192, verbose_name="SID",
                           validators=[validate_sid])

    @property
    def key(self):
        return 'filesystem-owner-sid'

    def __str__(self):
        return self.sid

    class Meta:
        verbose_name = "ADSID alias"
        verbose_name_plural = "ADSID aliases"
