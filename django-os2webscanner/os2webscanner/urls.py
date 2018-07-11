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
from django.conf.urls import url
from django.views.i18n import javascript_catalog
import django.contrib.auth.views

from .views.views import MainPageView
from .views.report_views import ScanReportLog, CSVReportDetails, ReportDetails, ReportList, ReportDelete
from .views.webscanner_views import WebScannerCreate, WebScannerUpdate, WebScannerDelete, WebScannerRun, \
    WebScannerAskRun, WebScannerList
from .views.filescanner_views import FileScannerCreate, FileScannerRun, FileScannerAskRun, FileScannerUpdate, \
    FileScannerDelete, FileScannerList
from .views.views import OrganizationUpdate, OrganizationList
from .views.domain_views import DomainValidate
from .views.exchangedomain_views import ExchangeDomainList
from .views.filedomain_views import FileDomainList, FileDomainCreate, FileDomainUpdate, FileDomainDelete
from .views.webdomain_views import WebDomainList, WebDomainCreate, WebDomainUpdate, WebDomainDelete
from .views.views import GroupList, GroupCreate, GroupUpdate, GroupDelete
from .views.rule_views import RuleList, RuleCreate, RuleUpdate, RuleDelete
from .views.views import SummaryList, SummaryCreate, SummaryUpdate, SummaryDelete
from .views.views import SummaryReport, DialogSuccess, SystemStatusView
from .views.views import file_upload, referrer_content
from .models.webscanner_model import WebScanner
from .models.filescanner_model import FileScanner


js_info_dict = {
    'packages': ('os2webscanner', 'recurrence')
}

urlpatterns = [
    # App URLs
    url(r'^$', MainPageView.as_view(), name='index'),
    url(r'^webscanners/$', WebScannerList.as_view(), name='webscanners'),
    url(r'^webscanners/add/$', WebScannerCreate.as_view(), name='webscanner_add'),
    url(r'^webscanners/(?P<pk>\d+)/delete/$', WebScannerDelete.as_view(),
        name='scanner_delete'),
    url(r'^webscanners/(?P<pk>\d+)/run/$', WebScannerRun.as_view(),
        name='webscanner_run'),
    url(r'^webscanners/(?P<pk>\d+)/askrun/$',
        WebScannerAskRun.as_view(
            template_name='os2webscanner/scanner_askrun.html',
            model=WebScanner),
        name='scanner_askrun'),
    url(r'^webscanners/(?P<pk>\d+)/$', WebScannerUpdate.as_view(),
        name='scanner_update'),
    url(r'^filescanners/$', FileScannerList.as_view(), name='filescanners'),
    url(r'^filescanners/add/$', FileScannerCreate.as_view(), name='filescanner_add'),
    url(r'^filescanners/(?P<pk>\d+)/delete/$', FileScannerDelete.as_view(),
        name='scanner_delete'),
    url(r'^filescanners/(?P<pk>\d+)/run/$', FileScannerRun.as_view(),
        name='scanner_run'),
    url(r'^filescanners/(?P<pk>\d+)/askrun/$',
        FileScannerAskRun.as_view(
            template_name='os2webscanner/scanner_askrun.html',
            model=FileScanner),
        name='scanner_askrun'),
    url(r'^exchangedomains/$', ExchangeDomainList.as_view(), name='exchangedomains'),
    url(r'^filescanners/(?P<pk>\d+)/$', FileScannerUpdate.as_view(),
        name='scanner_update'),
    url(r'^filedomains/$', FileDomainList.as_view(), name='filedomains'),
    url(r'^filedomains/add/$', FileDomainCreate.as_view(), name='filedomain_add'),
    url(r'^filedomains/(?P<pk>\d+)/validate/$', DomainValidate.as_view(),
        name='file_domain_validate'),
    url(r'^(filedomains)/(\d+)/(success)/$', DialogSuccess.as_view()),
    url(r'^filedomains/(?P<pk>\d+)/$', FileDomainUpdate.as_view(),
        name='file_domain_update'),
    url(r'^filedomains/(?P<pk>\d+)/delete/$', FileDomainDelete.as_view(),
        name='file_domain_delete'),
    url(r'^webdomains/$', WebDomainList.as_view(), name='webdomains'),
    url(r'^webdomains/add/$', WebDomainCreate.as_view(), name='webdomain_add'),
    url(r'^webdomains/(?P<pk>\d+)/validate/$', DomainValidate.as_view(),
        name='web_domain_validate'),
    url(r'^(webdomains)/(\d+)/(success)/$', DialogSuccess.as_view()),
    url(r'^webdomains/(?P<pk>\d+)/$', WebDomainUpdate.as_view(),
        name='web_domain_update'),
    url(r'^webdomains/(?P<pk>\d+)/delete/$', WebDomainDelete.as_view(),
        name='web_domain_delete'),
    url(r'^rules/$', RuleList.as_view(), name='rules'),
    url(r'^rules/add/$', RuleCreate.as_view(), name='rule_add'),
    url(r'^rules/(?P<pk>\d+)/$', RuleUpdate.as_view(),
        name='rule_update'),
    url(r'^rules/(?P<pk>\d+)/delete/$', RuleDelete.as_view(),
        name='rule_delete'),
    url(r"^rules/organization/$", OrganizationUpdate.as_view(),
        name='organization_update'),
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
    url(r'^reports/summaries/$', SummaryList.as_view(), name='summaries'),
    url(r'^reports/summaries/add/$', SummaryCreate.as_view(), name='summary_add'),
    url(r'^reports/summary/(?P<pk>\d+)/$', SummaryUpdate.as_view(),
        name='summary_update'),
    url(r'^reports/summary/(?P<pk>\d+)/report/$', SummaryReport.as_view(),
        name='summary_report'),
    url(r'^reports/summary/(?P<pk>\d+)/delete/$', SummaryDelete.as_view(),
        name='summary_delete'),
    # Login/logout stuff
    url(r'^accounts/login/', django.contrib.auth.views.login,
        {'template_name': 'login.html'}, name='login'),
    url(r'^accounts/logout/', django.contrib.auth.views.logout,
        {'template_name': 'logout.html'}, name='logout'),
    url(r'^accounts/password_change/',
        django.contrib.auth.views.password_change,
        {'template_name': 'password_change.html'},
        name='password_change'
        ),
    url(r'^accounts/password_change_done/',
        django.contrib.auth.views.password_change_done,
        {'template_name': 'password_change_done.html'},
        name='password_change_done'
        ),
    url(r'^accounts/password_reset/$',
        django.contrib.auth.views.password_reset,
        {'template_name': 'password_reset_form.html'},
        name='password_reset'
        ),
    url(r'^accounts/password_reset/done/',
        django.contrib.auth.views.password_reset_done,
        {'template_name': 'password_reset_done.html'},
        name='password_reset_done'
        ),
    url(r'^accounts/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/' +
        '(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/',
        django.contrib.auth.views.password_reset_confirm,
        {'template_name': 'password_reset_confirm.html'},
        name='password_reset_confirm'
        ),
    url(r'^accounts/reset/complete',
        django.contrib.auth.views.password_reset_complete,
        {'template_name': 'password_reset_complete.html'},
        name='password_reset_complete'
        ),

    # General dialog success handler
    url(r'^(webscanners|webdomains|rules|groups|reports/summaries)/(\d+)/(created)/$',
        DialogSuccess.as_view()),
    url(r'^(webscanners|webdomains|rules|groups|reports/summaries)/(\d+)/(saved)/$',
        DialogSuccess.as_view()),
    # General dialog success handler
    url(r'^(filescanners|filedomains|rules|groups|reports/summaries)/(\d+)/(created)/$',
        DialogSuccess.as_view()),
    url(r'^(filescanners|filedomains|rules|groups|reports/summaries)/(\d+)/(saved)/$',
        DialogSuccess.as_view()),
    url(r'^jsi18n/$', javascript_catalog, js_info_dict),
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
