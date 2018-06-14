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

from django.utils.translation import ugettext, ugettext_lazy as _

from django.conf import settings

from .models.authentication_model import Authentication
from .models.organization_model import Organization
from .models.userprofile_model import UserProfile
from .models.webdomain_model import WebDomain
from .models.filedomain_model import FileDomain
from .models.regexrule_model import RegexRule
from .models.scanner_model import Scanner
from .models.match_model import Match
from .models.url_model import Url
from .models.scan_model import Scan
from .models.conversionqueueitem_model import ConversionQueueItem
from .models.referrerurl_model import ReferrerUrl
from .models.urllastmodified_model import UrlLastModified
from .models.group_model import Group
from .models.md5sum_model import Md5Sum
from .models.statistic_model import Statistic

ar = admin.site.register
classes = [Authentication, Organization, WebDomain, FileDomain, RegexRule,
           Scanner, Scan, Match, Url, ConversionQueueItem, ReferrerUrl,
           UrlLastModified, Group, Md5Sum, Statistic]
list(map(ar, classes))


class ProfileInline(admin.TabularInline):

    """Inline class for user profiles."""

    model = UserProfile
    extra = 1
    if not settings.DO_USE_GROUPS:
        exclude = ['is_group_admin']
    can_delete = False

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)

        if db_field.name == 'organization':
            if not request.user.is_superuser:
                field.queryset = Organization.objects.filter(
                    name=request.user.profile.organization.name
                )
                field.empty_label = None

        return field


class MyUserAdmin(UserAdmin):

    """Custom user admin class."""

    inlines = [ProfileInline]
    can_delete = False

    def get_form(self, request, obj=None, **kwargs):
        if not request.user.is_superuser:
            self.fieldsets = (
                (None,
                 {'fields': ('username', 'password', 'is_active')}),
                (_('Personal info'),
                 {'fields': ('first_name', 'last_name', 'email')}),
                (_('Important dates'), {'fields': ('last_login',
                                                   'date_joined')}),
            )

            self.exclude = ['is_superuser', 'permissions', 'groups']
        return super().get_form(request, obj, **kwargs)

    def get_queryset(self, request):
        """Only allow users belonging to same organization to be edited."""

        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs
        return qs.filter(
            profile__organization=request.user.profile.organization
        )


admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)
