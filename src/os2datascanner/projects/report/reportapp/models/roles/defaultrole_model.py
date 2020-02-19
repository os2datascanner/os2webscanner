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

from django.db import models

from ..documentreport_model import DocumentReport
from .role_model import Role


class DefaultRole(Role):
    """The DefaultRole role's filter accepts all matches whose metadata can be
    associated with one of the user's aliases.

    (This role *can*, and should, be explicitly associated with users, but the
    system will also use its behaviour as a fallback if users don't have any
    other roles.)"""

    def filter(self, document_reports):
        aliases = self.user.aliases.select_subclasses()
        results = DocumentReport.objects.none()
        for alias in aliases:
            # TODO: Filter only where matched are True (waiting on test data)
            result = document_reports.filter(
                data__metadata__metadata__contains={
                    str(alias.key): str(alias)
                })
            # Merges django querysets together
            results = results | result
        return results
