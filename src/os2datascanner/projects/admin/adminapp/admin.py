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

from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from .models.authentication_model import Authentication
from .models.conversionqueueitem_model import ConversionQueueItem
from .models.group_model import Group
from .models.match_model import Match
from .models.organization_model import Organization
from .models.referrerurl_model import ReferrerUrl
from .models.regexpattern_model import RegexPattern
from .models.regexrule_model import RegexRule
from .models.scans.scan_model import Scan
from .models.scannerjobs.webscanner_model import WebScanner
from .models.scannerjobs.filescanner_model import FileScanner
from .models.scannerjobs.exchangescanner_model import ExchangeScanner
from .models.statistic_model import Statistic, TypeStatistics
from .models.webversion_model import WebVersion
from .models.urllastmodified_model import UrlLastModified
from .models.userprofile_model import UserProfile


@admin.register(Authentication)
class AuthenticationAdmin(admin.ModelAdmin):
    list_display = ('username', 'domain')


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('scan', 'sensitivity', 'url',)
    list_filter = ('sensitivity',)


@admin.register(RegexRule)
class RegexRuleAdmin(admin.ModelAdmin):
    list_filter = ('sensitivity',)
    list_display = ('name', 'organization', 'group', 'sensitivity')


@admin.register(RegexPattern)
class RegexPatternAdmin(admin.ModelAdmin):
    list_display = ('pattern_string', 'regex')


@admin.register(Scan)
class ScanAdmin(admin.ModelAdmin):
    date_hierarchy = 'start_time'
    list_display = ('scanner', 'status', 'start_time', 'end_time', 'is_visible')
    list_filter = ('status', 'is_visible', 'scanner')


class TypeStatisticsInline(admin.TabularInline):
    model = TypeStatistics


@admin.register(Statistic)
class StatisticAdmin(admin.ModelAdmin):
    inlines = (TypeStatisticsInline,)
    list_display = ('scan', 'files_scraped_count')


@admin.register(WebVersion)
class WebVersionAdmin(admin.ModelAdmin):
    list_filter = ('scan',)
    list_display = ('url', 'scan')

@admin.register(UrlLastModified)
class UrlModifiedAdmin(admin.ModelAdmin):
    date_hierarchy = 'last_modified'
    list_filter = ('scanner',)
    list_display = ('url', 'scanner', 'last_modified')

@admin.register(ConversionQueueItem)
class ConversionQueueItemAdmin(admin.ModelAdmin):
    date_hierarchy = 'process_start_time'
    list_filter = ('status',)
    list_display = ('file', 'type', 'page_no', 'status',
                    'process_start_time')

@admin.register(ReferrerUrl)
class ReferrerUrlAdmin(admin.ModelAdmin):
    list_display = ('url', 'scan')

for _cls in [
    Group, Organization, FileScanner, ExchangeScanner, WebScanner,
]:
    admin.site.register(_cls)


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
