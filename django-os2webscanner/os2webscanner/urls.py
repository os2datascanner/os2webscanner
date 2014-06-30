from django.conf.urls import patterns, url

from .views import MainPageView, ScannerList, DomainList, RuleList, ReportList

urlpatterns = patterns(
    '',
    url(r'^$', MainPageView.as_view(), name='index'),
    url(r'^scanners/$', ScannerList.as_view(), name='scanners'),
    url(r'^domains/$', DomainList.as_view(), name='domains'),
    url(r'^rules/$', RuleList.as_view(), name='rules'),
    url(r'^reports/$', ReportList.as_view(), name='reports'),
)
