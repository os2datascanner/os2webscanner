import django_saml2_auth.views
import django.contrib.auth.views
from django.conf.urls import url
from django.urls import include
from django.conf import settings

from .views.views import (MainPageView, RulePageView, ApprovalPageView,
                          StatsPageView, SettingsPageView, AboutPageView)

urlpatterns = [
    url(r'^$',      MainPageView.as_view(),     name="index"),
    url('rule/$',     RulePageView.as_view(),     name="rule"),
    url('approval', ApprovalPageView.as_view(), name="about"),
    url('stats',    StatsPageView.as_view(),    name="about"),
    url('settings', SettingsPageView.as_view(), name="settings"),
    url('about',    AboutPageView.as_view(),    name="about"),
]
if settings.SAML2_ENABLED:
    urlpatterns.append(url(r"^saml2_auth/", include("django_saml2_auth.urls")))
    urlpatterns.append(url(r"^accounts/login/$", django_saml2_auth.views.signin))
    urlpatterns.append(url(r'^accounts/logout/$', django_saml2_auth.views.signout))
else:
    urlpatterns.append(url(r'^accounts/login/',
        django.contrib.auth.views.LoginView.as_view(
            template_name='login.html',
        ),
        name='login'))
    urlpatterns.append(url(r'^accounts/logout/',
        django.contrib.auth.views.LogoutView.as_view(
            template_name='login.html',
        ),
        name='logout'))

