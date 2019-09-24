from django.conf.urls import url
from .views import ReportView
from .views import MainPageView

urlpatterns = [
    url(r'^$', MainPageView.as_view(), name="index"),
    url('report/', ReportView.as_view(), name="reports-all")
]
