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
"""Scrapy Items."""

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from os2datascanner.sites.admin.adminapp.models.match_model import Match

from scrapy.item import Field
from scrapy_djangoitem import DjangoItem


class MatchItem(DjangoItem):

    """Scrapy Item using the Match object from the Django model as storage."""

    django_model = Match

    """Original text matched. Stored temporarily for the purposes of
    replacing the original matched text.

    Note that this is not stored in the DB."""
    original_matched_data = Field()
