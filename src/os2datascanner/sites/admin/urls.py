"""URL patterns."""

import django_xmlrpc.views
from django.conf.urls import include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    # Include webscanner URLs
    url(r'^', include('os2datascanner.sites.admin.adminapp.urls')),
    # Enable admin
    url('^admin/', admin.site.urls),
    # XMLRPC
    url(r'^xmlrpc/$', django_xmlrpc.views.handle_xmlrpc, name='xmlrpc'),
]
