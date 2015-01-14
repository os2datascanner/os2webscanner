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

from django.conf import settings
from django.conf.urls import patterns, url
from django.views.i18n import javascript_catalog
from django.views.generic import View, ListView, TemplateView, DetailView

from .views import MainPageView, ScannerList, DomainList, RuleList
from .views import CSVReportDetails, ReportDetails, ReportList, ReportDelete
from .views import ScannerCreate, ScannerUpdate, ScannerDelete, ScannerRun
from .views import ScannerAskRun, ScanReportLog, OrganizationUpdate
from .views import DomainCreate, DomainUpdate, DomainValidate, DomainDelete
from .views import GroupList, GroupCreate, GroupUpdate, GroupDelete
from .views import RuleCreate, RuleUpdate, RuleDelete, OrganizationList
from .views import SummaryList, SummaryCreate, SummaryUpdate, SummaryDelete
from .views import SummaryReport
from .views import DialogSuccess
from .views import SystemStatusView
from .models import Scanner


js_info_dict = {
    'packages': ('os2webscanner', 'recurrence')
}

urlpatterns = patterns(
    '',
    # App URLs
    url(r'^$', MainPageView.as_view(), name='index'),
    url(r'^scanners/$', ScannerList.as_view(), name='scanners'),
    url(r'^scanners/add/$', ScannerCreate.as_view(), name='scanner_add'),
    url(r'^scanners/(?P<pk>\d+)/delete/$', ScannerDelete.as_view(),
        name='scanner_delete'),
    url(r'^scanners/(?P<pk>\d+)/run/$', ScannerRun.as_view(),
        name='scanner_run'),
    url(r'^scanners/(?P<pk>\d+)/askrun/$',
        ScannerAskRun.as_view(
            template_name='os2webscanner/scanner_askrun.html',
            model=Scanner),
        name='scanner_askrun'),
    url(r'^scanners/(?P<pk>\d+)/$', ScannerUpdate.as_view(),
        name='scanner_update'),
    url(r'^domains/$', DomainList.as_view(), name='domains'),
    url(r'^domains/add/$', DomainCreate.as_view(), name='domain_add'),
    url(r'^domains/(?P<pk>\d+)/validate/$', DomainValidate.as_view(),
        name='domain_validate'),
    url(r'^(domains)/(\d+)/(success)/$', DialogSuccess.as_view()),
    url(r'^domains/(?P<pk>\d+)/$', DomainUpdate.as_view(),
        name='domain_update'),
    url(r'^domains/(?P<pk>\d+)/delete/$', DomainDelete.as_view(),
        name='domain_delete'),
    url(r'^rules/$', RuleList.as_view(), name='rules'),
    url(r'^rules/add/$', RuleCreate.as_view(), name='rule_add'),
    url(r'^rules/(?P<pk>\d+)/$', RuleUpdate.as_view(),
        name='rule_update'),
    url(r'^rules/(?P<pk>\d+)/delete/$', RuleDelete.as_view(),
        name='rule_delete'),
    url(r'^reports/$', ReportList.as_view(), name='reports'),
    url(r'^report/(?P<pk>[0-9]+)/$', ReportDetails.as_view(),
        name='report'),
    url(r'^report/(?P<pk>[0-9]+)/full/$', ReportDetails.as_view(full=True),
        name='full_report'),
    url(r'^report/(?P<pk>[0-9]+)/csv/$', CSVReportDetails.as_view(),
        name='csvreport'),
    url(r'^report/(?P<pk>[0-9]+)/log/$', ScanReportLog.as_view(),
        name='logreport'),
    url(r'^report/(?P<pk>[0-9]+)/delete/$', ReportDelete.as_view(),
        name='report_delete'),
    url(r'^summaries/$', SummaryList.as_view(), name='summaries'),
    url(r'^summaries/add/$', SummaryCreate.as_view(), name='summary_add'),
    url(r'^summary/(?P<pk>\d+)/$', SummaryUpdate.as_view(),
        name='summary_update'),
    url(r'^summary/(?P<pk>\d+)/report/$', SummaryReport.as_view(),
        name='summary_report'),
    url(r'^summary/(?P<pk>\d+)/delete/$', SummaryDelete.as_view(),
        name='summary_delete'),
    url(r"^organization/$", OrganizationUpdate.as_view(),
        name='organization_update'),
    # Login/logout stuff
    url(r'^accounts/login/', 'django.contrib.auth.views.login',
        {'template_name': 'login.html'}, name='login'),
    url(r'^accounts/logout/', 'django.contrib.auth.views.logout',
        {'template_name': 'logout.html'}, name='logout'),
    url(r'^accounts/password_change/',
        'django.contrib.auth.views.password_change',
        {'template_name': 'password_change.html'},
        name='password_change'
    ),
    url(r'^accounts/password_change_done/',
        'django.contrib.auth.views.password_change_done',
        {'template_name': 'password_change_done.html'},
        name='password_change_done'
    ),

    # General dialog success handler
    url(r'^(scanners|domains|rules|groups|summaries)/(\d+)/(created)/$',
        DialogSuccess.as_view()),
    url(r'^(scanners|domains|rules|groups|summaries)/(\d+)/(saved)/$',
        DialogSuccess.as_view()),
    url(r'^jsi18n/$', javascript_catalog, js_info_dict),

    url(r'^system/status/?$', SystemStatusView.as_view()),
    url(r'^system/orgs_and_domains/$', OrganizationList.as_view(),
        name='orgs_and_domains'),
)

if settings.DO_USE_GROUPS:
    urlpatterns += patterns(
        '',
        url(r'^groups/$', GroupList.as_view(), name='groups'),
        url(r'^groups/add/$', GroupCreate.as_view(), name='group_add'),
        url(r'^(groups)/(\d+)/(success)/$', DialogSuccess.as_view()),
        url(r'^groups/(?P<pk>\d+)/$', GroupUpdate.as_view(),
            name='group_update'),
        url(r'^groups/(?P<pk>\d+)/delete/$', GroupDelete.as_view(),
            name='group_delete'),
    )
