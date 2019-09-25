from django.conf.urls import url

from .views import MainPageView
from .views import LoginPageView
from .views import ApprovalPageView
from .views import StatsPageView
from .views import SettingsPageView
from .views import AboutPageView

urlpatterns = [
    url(r'^$',      MainPageView.as_view(),     name="index"),
    url('login',    LoginPageView.as_view(),    name="login"),
    url('approval', ApprovalPageView.as_view(), name="about"),
    url('stats',    StatsPageView.as_view(),    name="about"),
    url('settings', SettingsPageView.as_view(), name="settings"),
    url('about',    AboutPageView.as_view(),    name="about")
]
