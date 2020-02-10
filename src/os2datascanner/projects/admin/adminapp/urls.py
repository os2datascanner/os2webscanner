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
"""URL mappings."""

import django.contrib.auth.views
from django.conf import settings
from django.conf.urls import url
from django.views.i18n import JavaScriptCatalog

from .models.scans.scan_model import Scan
from .models.scannerjobs.exchangescanner_model import ExchangeScanner
from .models.scannerjobs.filescanner_model import FileScanner
from .models.scannerjobs.webscanner_model import WebScanner
from .views.exchangescanner_views import ExchangeScannerList, ExchangeScannerCreate, ExchangeScannerUpdate, \
    ExchangeScannerDelete, ExchangeScannerRun, ExchangeScannerAskRun
from .views.filescanner_views import FileScannerCreate, FileScannerRun, FileScannerAskRun, FileScannerUpdate, \
    FileScannerDelete, FileScannerList
from .views.rule_views import RuleList, \
    CPRRuleCreate, CPRRuleUpdate, CPRRuleDelete, \
    RegexRuleCreate, RegexRuleUpdate, RegexRuleDelete
from .views.views import GroupList, GroupCreate, GroupUpdate, GroupDelete
from .views.views import MainPageView
from .views.views import OrganizationList
from .views.views import SummaryList, SummaryCreate, SummaryUpdate, SummaryDelete
from .views.views import SummaryReport, DialogSuccess, SystemStatusView
from .views.views import file_upload, referrer_content
from .views.webscanner_views import (WebScannerCreate, WebScannerUpdate,
                                     WebScannerDelete, WebScannerRun,
                                     WebScannerAskRun, WebScannerList,
                                     WebScannerValidate)

urlpatterns = [
    # App URLs
    url(r'^$', MainPageView.as_view(), name='index'),
    url(r'^exchangescanners/$', ExchangeScannerList.as_view(), name='exchangescanners'),
    url(r'^exchangescanners/add/$', ExchangeScannerCreate.as_view(), name='exchangescanner_add'),
    url(r'^exchangescanners/(?P<pk>\d+)/delete/$', ExchangeScannerDelete.as_view(),
        name='exchangescanner_delete'),
    url(r'^exchangescanners/(?P<pk>\d+)/$', ExchangeScannerUpdate.as_view(),
        name='exchangescanner_update'),
    url(r'^exchangescanners/(?P<pk>\d+)/run/$', ExchangeScannerRun.as_view(),
        name='exchangescanner_run'),
    url(r'^exchangescanners/(?P<pk>\d+)/askrun/$',
        ExchangeScannerAskRun.as_view(
            template_name='os2datascanner/scanner_askrun.html',
            model=ExchangeScanner),
        name='scanner_askrun'),
    url(r'^webscanners/$', WebScannerList.as_view(), name='webscanners'),
    url(r'^webscanners/add/$', WebScannerCreate.as_view(), name='webscanner_add'),
    url(r'^webscanners/(?P<pk>\d+)/delete/$', WebScannerDelete.as_view(),
        name='scanner_delete'),
    url(r'^webscanners/(?P<pk>\d+)/validate/$', WebScannerValidate.as_view(),
        name='web_scanner_validate'),
    url(r'^webscanners/(?P<pk>\d+)/run/$', WebScannerRun.as_view(),
        name='webscanner_run'),
    url(r'^webscanners/(?P<pk>\d+)/askrun/$',
        WebScannerAskRun.as_view(
            template_name='os2datascanner/scanner_askrun.html',
            model=WebScanner),
        name='scanner_askrun'),
    url(r'^webscanners/(?P<pk>\d+)/$', WebScannerUpdate.as_view(),
        name='scanner_update'),
    url(r'^filescanners/$', FileScannerList.as_view(), name='filescanners'),
    url(r'^filescanners/add/$', FileScannerCreate.as_view(), name='filescanner_add'),
    url(r'^filescanners/(?P<pk>\d+)/$', FileScannerUpdate.as_view(),
        name='scanner_update'),
    url(r'^filescanners/(?P<pk>\d+)/delete/$', FileScannerDelete.as_view(),
        name='scanner_delete'),
    url(r'^filescanners/(?P<pk>\d+)/run/$', FileScannerRun.as_view(),
        name='filescanner_run'),
    url(r'^filescanners/(?P<pk>\d+)/askrun/$',
        FileScannerAskRun.as_view(
            template_name='os2datascanner/scanner_askrun.html',
            model=FileScanner),
        name='filescanner_askrun'),
    url(r'^rules/$', RuleList.as_view(), name='rules'),
    url(r'^rules/cpr/add/$', CPRRuleCreate.as_view(), name='cprrule_add'),
    url(r'^rules/cpr/(?P<pk>\d+)/$', CPRRuleUpdate.as_view(),
        name='rule_update'),
    url(r'^rules/cpr/(?P<pk>\d+)/delete/$', CPRRuleDelete.as_view(),
        name='rule_delete'),
    url(r'^rules/regex/add/$', RegexRuleCreate.as_view(), name='regexrule_add'),
    url(r'^rules/regex/(?P<pk>\d+)/$', RegexRuleUpdate.as_view(),
        name='rule_update'),
    url(r'^rules/regex/(?P<pk>\d+)/delete/$', RegexRuleDelete.as_view(),
        name='rule_delete'),
    # Login/logout stuff
    url(r'^accounts/login/',
        django.contrib.auth.views.LoginView.as_view(
            template_name='login.html',
        ),
        name='login'),
    url(r'^accounts/logout/',
        django.contrib.auth.views.LogoutView.as_view(
            template_name='logout.html',
        ),
        name='logout'),
    url(r'^accounts/password_change/',
        django.contrib.auth.views.PasswordChangeView.as_view(
            template_name='password_change.html',
        ),
        name='password_change'
        ),
    url(r'^accounts/password_change_done/',
        django.contrib.auth.views.PasswordChangeDoneView.as_view(
            template_name='password_change_done.html',
        ),
        name='password_change_done'
        ),
    url(r'^accounts/password_reset/$',
        django.contrib.auth.views.PasswordResetView.as_view(
            template_name='password_reset_form.html',
        ),
        name='password_reset'
        ),
    url(r'^accounts/password_reset/done/',
        django.contrib.auth.views.PasswordResetDoneView.as_view(
            template_name='password_reset_done.html',
        ),
        name='password_reset_done'
        ),
    url(r'^accounts/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/' +
        '(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/',
        django.contrib.auth.views.PasswordResetConfirmView.as_view(
            template_name='password_reset_confirm.html',
        ),
        name='password_reset_confirm'
        ),
    url(r'^accounts/reset/complete',
        django.contrib.auth.views.PasswordResetCompleteView.as_view(
            template_name='password_reset_complete.html',
        ),
        name='password_reset_complete'
        ),

    # General success handler
    url(r'^(webscanners|filescanners|exchangescanners)/(\d+)/(created)/$',
        DialogSuccess.as_view()),
    url(r'^(webscanners|filescanners|exchangescanners)/(\d+)/(saved)/$',
        DialogSuccess.as_view()),
    url(r'^(rules/regex|rules/cpr|groups)/(\d+)/(created)/$',
        DialogSuccess.as_view()),
    url(r'^(rules/regex|rules/cpr|groups)/(\d+)/(saved)/$',
        DialogSuccess.as_view()),

    url(r'^jsi18n/$', JavaScriptCatalog.as_view(
        packages=('os2datascanner.projects.admin.adminapp', 'recurrence'),
    )),
    # System functions
    url(r'^system/status/?$', SystemStatusView.as_view()),
    url(r'^system/orgs_and_domains/$', OrganizationList.as_view(),
        name='orgs_and_domains'),
    url(r'system/upload_file', file_upload, name='file_upload'),

    # Referrer DOM content
    url(r'referrer/(?P<pk>[0-9]+)/$',
        referrer_content, name='referrer_content')

]

if settings.DO_USE_GROUPS:
    urlpatterns += [
        '',
        url(r'^groups/$', GroupList.as_view(), name='groups'),
        url(r'^groups/add/$', GroupCreate.as_view(), name='group_add'),
        url(r'^(groups)/(\d+)/(success)/$', DialogSuccess.as_view()),
        url(r'^groups/(?P<pk>\d+)/$', GroupUpdate.as_view(),
            name='group_update'),
        url(r'^groups/(?P<pk>\d+)/delete/$', GroupDelete.as_view(),
            name='group_delete'),
    ]
