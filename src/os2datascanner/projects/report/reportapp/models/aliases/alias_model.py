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
from abc import abstractmethod
from django.db import models
from django.contrib.auth.models import User
from model_utils.managers import InheritanceManager

class Alias(models.Model):
    objects = InheritanceManager()

    user = models.ForeignKey(User, null=False, verbose_name="Bruger",
                             related_name="aliases", on_delete=models.CASCADE)

    @property
    @abstractmethod
    def key(self):

        """Returns the metadata property name associated with this alias."""