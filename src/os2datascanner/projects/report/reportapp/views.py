from rest_framework import generics
from .models import DocumentReport
from .serializers import DocumentReportSerializer
from django.views.generic import TemplateView


# Create your views here.
class ReportView(generics.ListAPIView):
    queryset = DocumentReport.objects.all()
    serializer_class = DocumentReportSerializer


class LoginPageView(TemplateView):
    template_name = 'login.html'


class MainPageView(TemplateView):
    template_name = 'index.html'


class RulePageView(TemplateView):
    template_name = 'rule.html'


class ApprovalPageView(TemplateView):
    template_name = 'approval.html'


class StatsPageView(TemplateView):
    template_name = 'stats.html'


class SettingsPageView(TemplateView):
    template_name = 'settings.html'


class AboutPageView(TemplateView):
    template_name = 'about.html'
