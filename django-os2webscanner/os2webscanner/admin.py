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
"""Admin form configuration."""

from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

# Register your models here.

from .models import Organization, UserProfile, Domain, RegexRule, Scanner
from .models import Scan, Match, Url, ConversionQueueItem
from .models import ReferrerUrl, UrlLastModified, Group, Md5Sum

ar = admin.site.register
classes = [Organization, Domain, RegexRule, Scanner, Scan, Match, Url,
           ConversionQueueItem, ReferrerUrl, UrlLastModified, Group, Md5Sum]
map(ar, classes)


class ProfileInline(admin.TabularInline):

    """Inline class for user profiles."""

    model = UserProfile
    extra = 1


class MyUserAdmin(UserAdmin):

    """Custom user admin class."""

    inlines = [ProfileInline]
    can_delete = False

admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)
