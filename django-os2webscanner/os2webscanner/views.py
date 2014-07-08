"""Contains Django views."""

from django import forms
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404
from django.views.generic import View, ListView, TemplateView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.forms.models import modelform_factory

from validate import validate_domain, get_validation_str

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
        if user.is_superuser:
            return self.model.objects.all()
        else:
            try:
                profile = user.get_profile()
                return self.model.objects.filter(organization=profile.organization)
            except UserProfile.DoesNotExist:
                return self.model.objects.filter(organization=None)


class MainPageView(TemplateView, LoginRequiredMixin):

    """Display the main page."""

    template_name = 'index.html'


class ScannerList(RestrictedListView):

    """Displays list of scanners."""

    model = Scanner
    template_name = 'os2webscanner/scanners.html'


class DomainList(RestrictedListView):

    """Displays list of domains."""

    model = Domain
    template_name = 'os2webscanner/domains.html'

    def get_queryset(self):

        query_set = super(DomainList, self).get_queryset()

        return query_set.order_by('url', 'pk')


class RuleList(RestrictedListView):

    """Displays list of scanners."""

    model = RegexRule
    template_name = 'os2webscanner/rules.html'


class ReportList(RestrictedListView):

    """Displays list of scanners."""

    model = Scan
    template_name = 'os2webscanner/reports.html'

    def get_queryset(self):
        """Restrict to the organization of the logged-in user."""
        user = self.request.user
        if user.is_superuser:
            reports = self.model.objects.all()
        else:
            try:
                profile = user.get_profile()
                reports = self.model.objects.filter(
                    scanner__organization=profile.organization
                )
            except UserProfile.DoesNotExist:
                reports = self.model.objects.filter(
                    scanner__organization=None
                )
        return reports.order_by('-start_time')


# Create/Update/Delete Views.

class RestrictedCreateView(CreateView, LoginRequiredMixin):
    def get_form_fields(self):
        fields = [f for f in self.fields]

        if self.request.user.is_superuser:
            fields.append('organization')

        return fields

    def get_form(self, form_class):
        fields = self.get_form_fields()
        form_class = modelform_factory(self.model, fields=fields)
        kwargs = self.get_form_kwargs()
        return form_class(**kwargs)

    def form_valid(self, form):
        if not self.request.user.is_superuser:
            try:
                user_profile = self.request.user.get_profile()
            except UserProfile.DoesNotExist:
                raise PermissionDenied
            self.object = form.save(commit=False)
            self.object.organization = user_profile.organization

        return super(RestrictedCreateView, self).form_valid(form)


class ScannerCreate(RestrictedCreateView):

    """Create a scanner view."""

    model = Scanner
    fields = ['name', 'schedule', 'whitelisted_names', 'domains',
              'do_cpr_scan', 'do_name_scan', 'regex_rules']

    def get_success_url(self):
        return '/scanners/%s/created/' % self.object.pk


class ScannerUpdate(UpdateView, LoginRequiredMixin):

    """Update a scanner view."""

    model = Scanner
    fields = ['name', 'schedule', 'whitelisted_names', 'domains',
              'do_cpr_scan', 'do_name_scan', 'regex_rules']

    def get_success_url(self):
        return '/scanners/%s/saved/' % self.object.pk


class ScannerDelete(DeleteView, LoginRequiredMixin):

    """Delete a scanner view."""

    model = Scanner
    success_url = '/scanners/'


class ScannerRun(DetailView, LoginRequiredMixin):
    model = Scanner
    template_name = 'os2webscanner/scanner_run.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        result = self.object.run()
        context = self.get_context_data(object=self.object)
        context['success'] = not result is None
        context['scan'] = result

        return self.render_to_response(context)


class DomainCreate(RestrictedCreateView):

    """Create a domain view."""

    model = Domain
    fields = ['url', 'exclusion_rules', 'sitemap']

    def get_form_fields(self):
        fields = super(DomainCreate, self).get_form_fields()
        if self.request.user.is_superuser:
            fields.append('validation_status')
        return fields

    def get_form(self, form_class):
        form = super(DomainCreate, self).get_form(form_class)

        for fname in form.fields:
            f = form.fields[fname]
            f.widget.attrs['class'] = 'form-control'

        return form

    def get_success_url(self):
        return '/domains/%s/created/' % self.object.pk


class DomainUpdate(UpdateView, LoginRequiredMixin):

    """Update a domain view."""

    model = Domain
    fields = ['url', 'exclusion_rules', 'sitemap']

    def get_form(self, form_class):
        enabled_fields = [f for f in DomainUpdate.fields]
        if self.request.user.is_superuser:
            enabled_fields.append('validation_status')
            enabled_fields.append('organization')
        elif not self.object.validation_status:
            enabled_fields.append('validation_method')

        form_class = modelform_factory(self.model, fields=enabled_fields)
        kwargs = self.get_form_kwargs()
        form = form_class(**kwargs)

        for fname in form.fields:
            f = form.fields[fname]
            f.widget.attrs['class'] = 'form-control'

        if 'validation_method' in form.fields:
            vm_field = form.fields['validation_method']
            if vm_field:
                vm_field.widget = forms.RadioSelect(
                    choices=vm_field.widget.choices
                )
                vm_field.widget.attrs['class'] = 'validateradio'

        return form

    def form_valid(self, form):
        old_obj = Domain.objects.get(pk=self.object.pk)
        if old_obj.url != self.object.url:
            self.object.validation_status = Domain.INVALID

        if not self.request.user.is_superuser:
            user_profile = self.request.user.get_profile()
            self.object = form.save(commit=False)
            self.object.organization = user_profile.organization

        result = super(DomainUpdate, self).form_valid(form)

        return result

    def get_context_data(self, **kwargs):
        context = super(DomainUpdate, self).get_context_data(**kwargs)
        for value, desc in Domain.validation_method_choices:
            key = 'valid_txt_' + str(value)
            context[key] = get_validation_str(self.object, value)
        return context

    def get_success_url(self):
        url = self.object.get_absolute_url()
        if 'save_and_validate' in self.request.POST:
            return 'validate/'
        else:
            return '/domains/%s/saved/' % self.object.pk


class DomainValidate(DetailView, LoginRequiredMixin):
    model = Domain

    def get_context_data(self, **kwargs):
        context = super(DomainValidate, self).get_context_data(**kwargs)
        context['validation_status'] = self.object.validation_status
        if not self.object.validation_status:
            result = validate_domain(self.object)

            if result:
                self.object.validation_status = Domain.VALID
                self.object.save()

            context['validation_success'] = result

        return context


class DomainDelete(DeleteView, LoginRequiredMixin):

    """Delete a domain view."""

    model = Domain
    success_url = '/domains/'


class RuleCreate(RestrictedCreateView):

    """Create a rule view."""

    model = RegexRule
    fields = ['name', 'match_string', 'description', 'sensitivity']

    def get_form(self, form_class):
        form = super(RuleCreate, self).get_form(form_class)

        for fname in form.fields:
            f = form.fields[fname]
            f.widget.attrs['class'] = 'form-control'

        return form

    def get_success_url(self):
        return '/rules/%s/created/' % self.object.pk


class RuleUpdate(UpdateView, LoginRequiredMixin):

    """Update a rule view."""

    model = RegexRule

    def get_form(self, form_class):
        form = super(RuleUpdate, self).get_form(form_class)

        for fname in form.fields:
            f = form.fields[fname]
            f.widget.attrs['class'] = 'form-control'

        return form

    def get_success_url(self):
        return '/rules/%s/created/' % self.object.pk


class RuleDelete(DeleteView, LoginRequiredMixin):

    """Delete a rule view."""

    model = RegexRule
    success_url = '/rules/'


# Reports stuff
class ReportDetails(DetailView, LoginRequiredMixin):

    """Display a detailed report."""

    model = Scan
    template_name = 'os2webscanner/report.html'
    context_object_name = "scan"

    def get_context_data(self, **kwargs):
        """Add the scan's matches to the report context data."""
        context = super(ReportDetails, self).get_context_data(**kwargs)
        all_matches = Match.objects.filter(
            scan=self.get_object()
        ).order_by('-sensitivity', 'url', 'matched_rule', 'matched_data')

        context['matches'] = all_matches
        return context


class DialogSuccess(TemplateView):
    template_name = 'os2webscanner/dialogsuccess.html'

    type_map = {
        'domains': Domain,
        'scanners': Scanner,
        'rules': RegexRule
    }

    def get_context_data(self, **kwargs):
        context = super(DialogSuccess, self).get_context_data(**kwargs)
        model_type = self.args[0]
        pk = self.args[1]
        created = self.args[2] == 'created'
        if model_type not in self.type_map:
            raise Http404
        model = self.type_map[model_type]
        item = get_object_or_404(model, pk=pk)
        context['item_description'] = item.display_name
        context['action'] = "oprettet" if created else "gemt"
        context['reload_url'] = '/' + model_type + '/'
        return context
