"""URL patterns."""

from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    # Include webscanner URLs
    url(r'^', include('os2webscanner.urls')),
    # Enable admin
    url(r'^admin/', include(admin.site.urls)),
)
