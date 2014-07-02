from django.conf.urls import patterns, url

from .views import MainPageView, ScannerList, DomainList, RuleList, \
    ReportDetails, ReportList

urlpatterns = patterns(
    '',
    # App URLs
    url(r'^$', MainPageView.as_view(), name='index'),
    url(r'^scanners/$', ScannerList.as_view(), name='scanners'),
    url(r'^domains/$', DomainList.as_view(), name='domains'),
    url(r'^rules/$', RuleList.as_view(), name='rules'),
    url(r'^reports/$', ReportList.as_view(), name='reports'),
    url(r'^report/(?P<pk>[0-9]+)/$', ReportDetails.as_view(), name='report'),
    # Login/logout stuff
    url(r'^accounts/login/', 'django.contrib.auth.views.login',
        {'template_name': 'login.html'}, name='login'),
    url(r'^accounts/logout/', 'django.contrib.auth.views.logout',
        {'template_name': 'logout.html'}, name='logout'),

)
