# encoding: utf-8
# The contents of this file are subject to the Mozilla Public License
# Version 2.0 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
#    http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# OS2Webscanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (http://www.os2web.dk/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( http://www.os2web.dk/ )
"""Contains Django views."""

import csv
from django import forms
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.http import Http404, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.views.generic import View, ListView, TemplateView, DetailView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.forms.models import modelform_factory
from django.conf import settings

from .validate import validate_domain, get_validation_str

from .models import Scanner, Domain, RegexRule, Scan, Match, UserProfile, Url
from .models import Organization


class LoginRequiredMixin(View):

    """Include to require login."""

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        """Check for login and dispatch the view."""
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
                return self.model.objects.filter(
                    organization=profile.organization
                )
            except UserProfile.DoesNotExist:
                return self.model.objects.filter(organization=None)


class MainPageView(TemplateView, LoginRequiredMixin):

    """Display the main page."""

    template_name = 'index.html'


class OrganizationList(RestrictedListView):

    """Display a list of organizations, superusers only!"""

    model = Organization
    template_name = 'os2webscanner/organizations_and_domains.html'

    def get_context_data(self, **kwargs):
        """Setup context for the template."""
        context = super(OrganizationList, self).get_context_data(**kwargs)
        organization_list = context['organization_list']
        orgs_with_domains = []
        for org in organization_list:
            tld_list = []

            tlds = set(['.'.join(d.url.split('.')[-2:]) for d in
                        org.domains.all()])
            for tld in tlds:
                tld_domains = [d.url for d in org.domains.all() if
                               d.url.split('.')[-2:] == tld.split('.')]
                tld_list.append({'tld': tld, 'domains': tld_domains})

            orgs_with_domains.append({'name': org.name, 'domains': tld_list})

        context['orgs_with_domains'] = orgs_with_domains
        print context

        return context


class ScannerList(RestrictedListView):

    """Displays list of scanners."""

    model = Scanner
    template_name = 'os2webscanner/scanners.html'

    def get_queryset(self):
        """Get queryset, don't include non-visible scanners."""
        qs = super(ScannerList, self).get_queryset()
        return qs.filter(is_visible=True)


class DomainList(RestrictedListView):

    """Displays list of domains."""

    model = Domain
    template_name = 'os2webscanner/domains.html'

    def get_queryset(self):
        """Get queryset, ordered by url followed by primary key."""
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
        reports = reports.filter(scanner__is_visible=True)
        return reports.order_by('-start_time')


# Create/Update/Delete Views.

class RestrictedCreateView(CreateView, LoginRequiredMixin):

    """Base class for create views that are limited by user organization."""

    def get_form_fields(self):
        """Get the list of fields to use in the form for the view."""
        fields = [f for f in self.fields]

        if self.request.user.is_superuser:
            fields.append('organization')

        return fields

    def get_form(self, form_class):
        """Get the form for the view."""
        fields = self.get_form_fields()
        form_class = modelform_factory(self.model, fields=fields)
        kwargs = self.get_form_kwargs()
        return form_class(**kwargs)

    def form_valid(self, form):
        """Validate the form."""
        if not self.request.user.is_superuser:
            try:
                user_profile = self.request.user.get_profile()
            except UserProfile.DoesNotExist:
                raise PermissionDenied
            self.object = form.save(commit=False)
            self.object.organization = user_profile.organization

        return super(RestrictedCreateView, self).form_valid(form)


class OrgRestrictedMixin(SingleObjectMixin, LoginRequiredMixin):

    """Mixin class for views with organization-restricted queryset."""

    def get_queryset(self):
        """Get queryset filtered by user's organiztion."""
        queryset = super(OrgRestrictedMixin, self).get_queryset()
        if not self.request.user.is_superuser:
            organization = None

            try:
                user_profile = self.request.user.get_profile()
                organization = user_profile.organization
            except UserProfile.DoesNotExist:
                organization = None

            queryset = queryset.filter(organization=organization)
        return queryset


class RestrictedUpdateView(UpdateView, OrgRestrictedMixin):

    """Base class for updateviews restricted by organiztion."""

    pass


class RestrictedDetailView(DetailView, OrgRestrictedMixin):

    """Base class for detailviews restricted by organiztion."""

    pass


class RestrictedDeleteView(DeleteView, OrgRestrictedMixin):

    """Base class for deleteviews restricted by organiztion."""

    pass


class ScannerCreate(RestrictedCreateView):

    """Create a scanner view."""

    model = Scanner
    fields = ['name', 'schedule', 'whitelisted_names', 'domains',
              'do_cpr_scan', 'do_cpr_modulus11', 'do_name_scan', 'do_ocr',
              'do_link_check', 'do_external_link_check',
              'do_last_modified_check', 'do_last_modified_check_head_request',
              'regex_rules']

    def get_form(self, form_class):
        """Get the form for the view.

        Querysets used for choices in the 'domains' and 'regex_rules' fields
        will be limited by the user's organiztion unless the user is a
        superuser.
        """
        form = super(ScannerCreate, self).get_form(form_class)
        try:
            organization = self.request.user.get_profile().organization
        except UserProfile.DoesNotExist:
            organization = None

        if not self.request.user.is_superuser:
            for field_name in ['domains', 'regex_rules']:
                queryset = form.fields[field_name].queryset
                queryset = queryset.filter(organization=organization)
                form.fields[field_name].queryset = queryset
        return form

    def get_success_url(self):
        """The URL to redirect to after successful creation."""
        return '/scanners/%s/created/' % self.object.pk


class ScannerUpdate(RestrictedUpdateView):

    """Update a scanner view."""

    model = Scanner
    fields = ['name', 'schedule', 'whitelisted_names', 'domains',
              'do_cpr_scan', 'do_cpr_modulus11', 'do_name_scan', 'do_ocr',
              'do_link_check', 'do_external_link_check',
              'do_last_modified_check', 'do_last_modified_check_head_request',
              'regex_rules']

    def get_success_url(self):
        """The URL to redirect to after successful update."""
        return '/scanners/%s/saved/' % self.object.pk

    def get_form(self, form_class):
        """Get the form for the view.

        Querysets used for choices in the 'domains' and 'regex_rules' fields
        will be limited by the user's organiztion unless the user is a
        superuser.
        """
        form = super(ScannerUpdate, self).get_form(form_class)
        scanner = self.get_object()

        for field_name in ['domains', 'regex_rules']:
            queryset = form.fields[field_name].queryset
            queryset = queryset.filter(organization=scanner.organization)
            form.fields[field_name].queryset = queryset

        return form


class ScannerDelete(RestrictedDeleteView):

    """Delete a scanner view."""

    model = Scanner
    success_url = '/scanners/'


class ScannerRun(RestrictedDetailView):

    """View that handles starting of a scanner run."""

    model = Scanner
    template_name = 'os2webscanner/scanner_run.html'

    def get(self, request, *args, **kwargs):
        """Handle a get request to the view."""
        self.object = self.get_object()

        result = self.object.run()
        context = self.get_context_data(object=self.object)
        context['success'] = not result is None
        context['scan'] = result

        return self.render_to_response(context)


class DomainCreate(RestrictedCreateView):

    """Create a domain view."""

    model = Domain
    fields = ['url', 'exclusion_rules', 'download_sitemap', 'sitemap_url',
              'sitemap']

    def get_form_fields(self):
        """Get the list of form fields.

        The 'validation_status' field will be added to the form if the
        user is a superuser.
        """
        fields = super(DomainCreate, self).get_form_fields()
        if self.request.user.is_superuser:
            fields.append('validation_status')
        return fields

    def get_form(self, form_class):
        """Get the form for the view.

        All form widgets will have added the css class 'form-control'.
        """
        form = super(DomainCreate, self).get_form(form_class)

        for fname in form.fields:
            f = form.fields[fname]
            f.widget.attrs['class'] = 'form-control'

        return form

    def get_success_url(self):
        """The URL to redirect to after successful creation."""
        return '/domains/%s/created/' % self.object.pk


class DomainUpdate(RestrictedUpdateView):

    """Update a domain view."""

    model = Domain
    fields = ['url', 'exclusion_rules', 'download_sitemap', 'sitemap_url',
              'sitemap']

    def get_form(self, form_class):
        """Get the form for the view.

        If the user is a superuser the fields  'validation_status' and
        'organization' will be added to the form.
        If the user is not a superuser and the domain has not been validated
        the 'validation_method' field will be added to the form.
        """
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
        """Validate the submitted form."""
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
        """Get the context used when rendering the template."""
        context = super(DomainUpdate, self).get_context_data(**kwargs)
        for value, desc in Domain.validation_method_choices:
            key = 'valid_txt_' + str(value)
            context[key] = get_validation_str(self.object, value)
        return context

    def get_success_url(self):
        """The URL to redirect to after successful updating.

        Will redirect the user to the validate view if the form was submitted
        with the 'save_and_validate' button.
        """
        url = self.object.get_absolute_url()
        if 'save_and_validate' in self.request.POST:
            return 'validate/'
        else:
            return '/domains/%s/saved/' % self.object.pk


class DomainValidate(RestrictedDetailView):

    """View that handles validation of a domain."""

    model = Domain

    def get_context_data(self, **kwargs):
        """Perform validation and populate the template context."""
        context = super(DomainValidate, self).get_context_data(**kwargs)
        context['validation_status'] = self.object.validation_status
        if not self.object.validation_status:
            result = validate_domain(self.object)

            if result:
                self.object.validation_status = Domain.VALID
                self.object.save()

            context['validation_success'] = result

        return context


class DomainDelete(RestrictedDeleteView):

    """Delete a domain view."""

    model = Domain
    success_url = '/domains/'


class RuleCreate(RestrictedCreateView):

    """Create a rule view."""

    model = RegexRule
    fields = ['name', 'match_string', 'description', 'sensitivity']

    def get_form(self, form_class):
        """Get the form for the view.

        All form fields will have the css class 'form-control' added.
        """
        form = super(RuleCreate, self).get_form(form_class)

        for fname in form.fields:
            f = form.fields[fname]
            f.widget.attrs['class'] = 'form-control'

        return form

    def get_success_url(self):
        """The URL to redirect to after successful creation."""
        return '/rules/%s/created/' % self.object.pk


class RuleUpdate(RestrictedUpdateView):

    """Update a rule view."""

    model = RegexRule

    def get_form(self, form_class):
        """Get the form for the view.

        All form fields will have the css class 'form-control' added.
        """
        form = super(RuleUpdate, self).get_form(form_class)

        for fname in form.fields:
            f = form.fields[fname]
            f.widget.attrs['class'] = 'form-control'

        return form

    def get_success_url(self):
        """The URL to redirect to after successful update."""
        return '/rules/%s/created/' % self.object.pk


class RuleDelete(RestrictedDeleteView):

    """Delete a rule view."""

    model = RegexRule
    success_url = '/rules/'


# Reports stuff
class ReportDetails(UpdateView, LoginRequiredMixin):

    """Display a detailed report summary."""

    model = Scan
    template_name = 'os2webscanner/report.html'
    context_object_name = "scan"
    full = False

    def get_queryset(self):
        """Get the queryset for the view.

        If the user is not a superuser the queryset will be limited by the
        user's organization.
        """
        queryset = super(ReportDetails, self).get_queryset()
        if not self.request.user.is_superuser:
            try:
                user_profile = self.request.user.get_profile()
                organization = user_profile.organization
            except UserProfile.DoesNotExist:
                organization = None
            queryset = queryset.filter(scanner__organization=organization)
        return queryset

    def get_context_data(self, **kwargs):
        """Add the scan's matches to the report context data."""
        context = super(ReportDetails, self).get_context_data(**kwargs)
        all_matches = Match.objects.filter(
            scan=self.get_object()
        ).order_by('-sensitivity', 'url', 'matched_rule', 'matched_data')

        broken_urls = Url.objects.filter(
            scan=self.get_object()
        ).exclude(status_code__isnull=True).order_by('url')

        context['full_report'] = self.full
        context['broken_urls'] = broken_urls
        context['no_of_broken_links'] = broken_urls.count()
        context['matches'] = all_matches[:100]
        context['all_matches'] = all_matches
        context['no_of_matches'] = all_matches.count() + broken_urls.count()
        context['reports_url'] = settings.SITE_URL + '/reports/'
        context['failed_conversions'] = (
            self.object.get_number_of_failed_conversions()
        )
        return context


class ReportDelete(DeleteView, LoginRequiredMixin):

    """View for deleting a report."""

    model = Scan
    success_url = '/reports/'

    def get_queryset(self):
        """Get the queryset for the view.

        If the user is not a superuser the queryset will be limited by the
        user's organization.
        """
        queryset = super(ReportDelete, self).get_queryset()
        if not self.request.user.is_superuser:
            try:
                user_profile = self.request.user.get_profile()
                organization = user_profile.organization
            except UserProfile.DoesNotExist:
                organization = None
            queryset = queryset.filter(scanner__organization=organization)
        return queryset


class CSVReportDetails(ReportDetails):

    """Display  full report in CSV format."""

    def render_to_response(self, context, **response_kwargs):
        """Generate a CSV file and return it as the http response."""
        scan = self.get_object()
        response = HttpResponse(content_type='text/csv')
        report_file = u'{0}{1}.csv'.format(
            scan.scanner.organization.name.replace(u' ', u'_'),
            scan.id)
        response[
            'Content-Disposition'
        ] = u'attachment; filename={0}'.format(report_file)
        writer = csv.writer(response)
        all_matches = context['all_matches']
        # CSV utilities
        e = lambda fields: ([f.encode('utf-8') for f in fields])
        # Print summary header
        writer.writerow(e([u'Starttidspunkt', u'Sluttidspunkt', u'Status',
                        u'Totalt antal matches', u'Total antal broken links']))
        # Print summary
        writer.writerow(e([str(scan.start_time),
            str(scan.end_time), scan.get_status_display(),
            str(context['no_of_matches']), str(context['no_of_broken_links'])])
        )
        if all_matches:
            # Print match header
            writer.writerow(e([u'URL', u'Regel', u'Match', u'Følsomhed']))
            for match in all_matches:
                writer.writerow(
                    e([match.url.url,
                       match.get_matched_rule_display(),
                       match.matched_data.replace('\n', '').replace('\r', ' '),
                       match.get_sensitivity_display()])
                )
        broken_urls = context['broken_urls']
        if broken_urls:
            # Print broken link header
            writer.writerow(e([u'Referrers', u'URL', u'Status']))
            for url in broken_urls:
                for referrer in url.referrers.all():
                    writer.writerow(e([referrer.url,
                                   url.url,
                                   url.status_message]))
        return response


class DialogSuccess(TemplateView):

    """View that handles success for iframe-based dialogs."""

    template_name = 'os2webscanner/dialogsuccess.html'

    type_map = {
        'domains': Domain,
        'scanners': Scanner,
        'rules': RegexRule
    }

    def get_context_data(self, **kwargs):
        """Setup context for the template."""
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
