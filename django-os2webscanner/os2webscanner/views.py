from django.shortcuts import render
from django.views.generic import View, ListView, TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from .models import Scanner, Domain, RegexRule, Scan, UserProfile


class LoginRequiredMixin(View):
    """Include to require login."""

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)


class RestrictedListView(ListView, LoginRequiredMixin):
    """Make sure users only see data that belong to their own organization."""
    
    def get_queryset(self):
        """Restrict to the organization of the logged-in user."""
        user = self.request.user
        try:
            profile = user.get_profile()
        except UserProfile.DoesNotExist:
            profile = None

        if profile:
            return self.model.objects.filter(organization=profile.organization)
        else:
            return self.model.objects.all()


class MainPageView(TemplateView):
    template_name = 'index.html'


class ScannerList(RestrictedListView):
    """Displays list of scanners."""
    model = Scanner
    template_name = 'os2webscanner/scanners.html'


class DomainList(RestrictedListView):
    """Displays list of domains."""
    model = Domain
    template_name = 'os2webscanner/domains.html'


class RuleList(RestrictedListView):
    """Displays list of scanners."""
    model = RegexRule
    template_name = 'os2webscanner/rules.html'


class ReportList(ListView, LoginRequiredMixin):
    """Displays list of scanners."""
    model = Scan
    template_name = 'os2webscanner/reports.html'
