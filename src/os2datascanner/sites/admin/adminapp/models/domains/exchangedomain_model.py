# -*- coding: utf-8 -*-
# encoding: utf-8
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
import logging
from django.conf import settings
from django.db import models

from .domain_model import Domain

# Get an instance of a logger
logger = logging.getLogger(__name__)


class ExchangeDomain(Domain):

    """Represents an exchange domain to be scanned.
    The domain url property is the mail ending. Example: @magenta.dk
    """

    userlist = models.FileField(upload_to='mailscan/users/')

    dir_to_scan = models.CharField(max_length=2048,
                                   verbose_name='Exchange export sti',
                                   null=True)

    def get_userlist_file_path(self):
        return os.path.join(settings.MEDIA_ROOT, self.userlist.name)

    class Meta:
        db_table = 'os2webscanner_exchangedomain'
