from operator import attrgetter

from django.shortcuts import render
from django.views.generic import View, ListView, TemplateView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from .models import Scanner, Domain, RegexRule, Scan, Match, UserProfile


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


# Create/Update/Delete Views.

class ScannerCreate(CreateView, LoginRequiredMixin):
    model = Scanner
    fields = ['name', 'schedule', 'whitelisted_names', 'domains',
              'do_cpr_scan', 'do_name_scan', 'regex_rules']

    def form_valid(self, form):
        user_profile = self.request.user.get_profile()
        self.object = form.save(commit=False)
        self.object.organization = user_profile.organization

        return super(ScannerCreate, self).form_valid(form)


class ScannerUpdate(UpdateView, LoginRequiredMixin):
    model = Scanner
    fields = ['name', 'schedule', 'whitelisted_names', 'domains',
              'do_cpr_scan', 'do_name_scan', 'regex_rules']


class ScannerDelete(DeleteView, LoginRequiredMixin):
    model = Scanner
    success_url = '/scanners/'


class DomainCreate(CreateView, LoginRequiredMixin):
    model = Domain
    fields = ['url', 'validation_status', 'validation_method',
              'exclusion_rules', 'sitemap']

    def form_valid(self, form):
        user_profile = self.request.user.get_profile()
        self.object = form.save(commit=False)
        self.object.organization = user_profile.organization

        return super(DomainCreate, self).form_valid(form)


class DomainUpdate(UpdateView, LoginRequiredMixin):
    model = Domain
    fields = ['url', 'validation_status', 'validation_method',
              'exclusion_rules', 'sitemap']


class DomainDelete(DeleteView, LoginRequiredMixin):
    model = Domain
    success_url = '/domains/'


class RuleCreate(CreateView, LoginRequiredMixin):
    model = RegexRule
    fields = ['name', 'match_string', 'description', 'sensitivity']

    def form_valid(self, form):
        user_profile = self.request.user.get_profile()
        self.object = form.save(commit=False)
        self.object.organization = user_profile.organization

        return super(RuleCreate, self).form_valid(form)


class RuleUpdate(UpdateView, LoginRequiredMixin):
    model = RegexRule


class RuleDelete(DeleteView, LoginRequiredMixin):
    model = RegexRule
    success_url = '/rules/'


# Reports stuff
class ReportDetails(DetailView, LoginRequiredMixin):
    """Display a detailed report."""
    model = Scan
    template_name = 'os2webscanner/report.html'
    context_object_name = "scan"

    def get_context_data(self, **kwargs):
        context = super(ReportDetails, self).get_context_data(**kwargs)
        all_matches = Match.objects.filter(
            scan=self.get_object()
        ).order_by('-sensitivity', 'url', 'matched_rule', 'matched_data')

        context['matches'] = all_matches
        return context
