import django.contrib.auth.views
from django.conf.urls import url

from .views.views import (MainPageView, RulePageView, ApprovalPageView,
                          StatsPageView, SettingsPageView, AboutPageView)

urlpatterns = [
    url(r'^$',      MainPageView.as_view(),     name="index"),
    url('rule',     RulePageView.as_view(),     name="rule"),
    url('approval', ApprovalPageView.as_view(), name="about"),
    url('stats',    StatsPageView.as_view(),    name="about"),
    url('settings', SettingsPageView.as_view(), name="settings"),
    url('about',    AboutPageView.as_view(),    name="about"),
    url(r'^accounts/login/',
        django.contrib.auth.views.LoginView.as_view(
            template_name='login.html',
        ),
        name='login'),
    url(r'^accounts/logout/',
        django.contrib.auth.views.LogoutView.as_view(
            template_name='login.html',
        ),
        name='logout'),
]

