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

import os
import csv
import tempfile
import codecs
from shutil import copyfile

from django import forms
from django.template import RequestContext
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.shortcuts import redirect
from django.views.generic import View, ListView, TemplateView, DetailView
from django.views.generic.edit import ModelFormMixin, DeleteView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.forms.models import modelform_factory
from django.conf import settings

from .validate import validate_domain, get_validation_str

from .models import Scanner, Domain, RegexRule, Scan, Match, UserProfile, Url
from .models import Organization, ConversionQueueItem, Group, Summary
from .models import ReferrerUrl
from .utils import scans_for_summary_report, do_scan
from .forms import FileUploadForm


class LoginRequiredMixin(View):

    """Include to require login.

    If user is "upload only", redirect to upload page."""

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        """Check for login and dispatch the view."""
        user = self.request.user
        try:
            profile = user.profile
            if profile.is_upload_only:
                return redirect('system/upload_file')
        except UserProfile.DoesNotExist:
            # User is *not* "upload only", all is good
            pass
        return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)


class SuperUserRequiredMixin(LoginRequiredMixin):

    """Include to require login and superuser."""

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        """Check for login and superuser and dispatch the view."""
        user = self.request.user
        if user.is_superuser:
            return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)
        else:
            raise PermissionDenied


class RestrictedListView(ListView, LoginRequiredMixin):

    """Make sure users only see data that belong to their own organization."""

    def get_queryset(self):
        """Restrict to the organization of the logged-in user."""
        user = self.request.user
        if user.is_superuser:
            return self.model.objects.all()
        else:
            try:
                profile = user.profile
                if profile.organization.do_use_groups:
                    if profile.is_group_admin or self.model == Group:
                        return self.model.objects.filter(
                            organization=profile.organization
                        )
                    else:
                        groups = profile.groups.all()
                        qs = self.model.objects.filter(
                            organization=profile.organization
                        ).filter(
                            Q(group__in=groups) | Q(group__isnull=True)
                        )
                        return qs
                else:
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

            def top_level(d):
                return '.'.join(d.strip('/').split('.')[-2:])
            tlds = set([top_level(d.url) for d in org.domains.all()])

            for tld in tlds:
                sub_domains = [
                    d.url for d in org.domains.all() if top_level(d.url) == tld
                ]
                tld_list.append({'tld': tld, 'domains': sub_domains})

            orgs_with_domains.append({'name': org.name, 'domains': tld_list})

        context['orgs_with_domains'] = orgs_with_domains

        return context


class ScannerList(RestrictedListView):

    """Displays list of scanners."""

    model = Scanner
    template_name = 'os2webscanner/scanners.html'

    def get_queryset(self):
        """Get queryset, don't include non-visible scanners."""
        qs = super(ScannerList, self).get_queryset()
        # Dismiss scans that are not visible
        qs = qs.filter(is_visible=True)
        return qs


class DomainList(RestrictedListView):

    """Displays list of domains."""

    model = Domain
    template_name = 'os2webscanner/domains.html'

    def get_queryset(self):
        """Get queryset, ordered by url followed by primary key."""
        query_set = super(DomainList, self).get_queryset()

        if query_set:
            query_set = query_set.order_by('url', 'pk')

        return query_set


class GroupList(RestrictedListView):
    """Displays groups for organization."""

    model = Group
    template_name = 'os2webscanner/groups.html'


class RuleList(RestrictedListView):

    """Displays list of scanners."""

    model = RegexRule
    template_name = 'os2webscanner/rules.html'


class ReportList(RestrictedListView):

    """Displays list of scanners."""

    model = Scan
    template_name = 'os2webscanner/reports.html'
    paginate_by = 20

    def get_queryset(self):
        """Restrict to the organization of the logged-in user."""
        user = self.request.user
        if user.is_superuser:
            reports = self.model.objects.all()
        else:
            try:
                profile = user.profile
                # TODO: Filter by group here if relevant.
                if (
                    profile.is_group_admin or not
                    profile.organization.do_use_groups
                ):
                    reports = self.model.objects.filter(
                        scanner__organization=profile.organization
                    )
                else:
                    reports = self.model.objects.filter(
                        scanner__group__in=profile.groups.all()
                    )
            except UserProfile.DoesNotExist:
                reports = self.model.objects.filter(
                    scanner__organization=None
                )
        reports = reports.filter(is_visible=True)
        return reports.order_by('-start_time')


# Create/Update/Delete Views.

class RestrictedCreateView(CreateView, LoginRequiredMixin):

    """Base class for create views that are limited by user organization."""

    def get_form_fields(self):
        """Get the list of fields to use in the form for the view."""
        fields = [f for f in self.fields]
        user = self.request.user

        if user.is_superuser:
            fields.append('organization')
        elif user.profile.organization.do_use_groups:
            if (
                user.profile.is_group_admin or
                len(user.profile.groups.all()) > 1
            ):
                fields.append('group')

        return fields

    def get_form(self, form_class):
        """Get the form for the view."""
        fields = self.get_form_fields()
        form_class = modelform_factory(self.model, fields=fields)
        kwargs = self.get_form_kwargs()

        form = form_class(**kwargs)
        user = self.request.user
        if 'group' in fields:
            if user.profile.is_group_admin:
                queryset = (
                    user.profile.organization.groups.all()
                )
            else:
                form.fields['group'].queryset = (
                    user.profile.groups.all()
                )
            form.fields['group'].queryset = queryset
        return form

    def form_valid(self, form):
        """Validate the form."""
        if not self.request.user.is_superuser:
            try:
                user_profile = self.request.user.profile
            except UserProfile.DoesNotExist:
                raise PermissionDenied
            self.object = form.save(commit=False)
            self.object.organization = user_profile.organization
            if (
                user_profile.organization.do_use_groups and not
                user_profile.is_group_admin and
                len(user_profile.groups.all())
            ):
                self.object.group = user_profile.groups.all()[0]

        return super(RestrictedCreateView, self).form_valid(form)


class OrgRestrictedMixin(ModelFormMixin, LoginRequiredMixin):

    """Mixin class for views with organization-restricted queryset."""

    def get_form_fields(self):
        """Get the list of fields to use in the form for the view."""
        fields = [f for f in self.fields]
        user = self.request.user
        organization = self.object.organization
        do_add_group = False
        if user.is_superuser:
            fields.append('organization')
        if organization.do_use_groups:
            if (
                user.is_superuser or
                user.profile.is_group_admin or
                len(user.profile.groups.all()) > 1
            ):
                do_add_group = True
        if do_add_group and self.model != Group:
            fields.append('group')
        return fields

    def get_form(self, form_class):
        """Get the form for the view."""
        fields = self.get_form_fields()
        form_class = modelform_factory(self.model, fields=fields)
        kwargs = self.get_form_kwargs()

        form = form_class(**kwargs)
        user = self.request.user
        if 'group' in fields:
            if user.is_superuser or user.profile.is_group_admin:
                form.fields['group'].queryset = (
                    self.object.organization.groups.all()
                )
            else:
                form.fields['group'].queryset = (
                    user.profile.groups.all()
                )
        return form

    def get_queryset(self):
        """Get queryset filtered by user's organization."""
        queryset = super(OrgRestrictedMixin, self).get_queryset()
        if not self.request.user.is_superuser:
            organization = None

            try:
                user_profile = self.request.user.profile
                organization = user_profile.organization
                groups = user_profile.groups.all()
            except UserProfile.DoesNotExist:
                organization = None
                groups = []

            if (
                user_profile.organization.do_use_groups and not
                user_profile.is_group_admin
            ):
                queryset = queryset.filter(
                    Q(group__in=groups) | Q(group__isnull=True)
                )
            else:
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


class OrganizationUpdate(UpdateView, LoginRequiredMixin):

    """Create an organization update view."""

    model = Organization
    fields = ['name_whitelist', 'name_blacklist', 'address_whitelist',
              'address_blacklist', 'cpr_whitelist']

    def get_object(self):
        """Get the organization to which the current user belongs."""
        try:
            object = self.request.user.profile.organization
        except UserProfile.DoesNotExist:
            object = None
        return object

    def get_success_url(self):
        return "/organization/"


class ScannerCreate(RestrictedCreateView):

    """Create a scanner view."""

    model = Scanner
    fields = ['name', 'schedule', 'domains',
              'do_cpr_scan', 'do_cpr_modulus11', 'do_cpr_ignore_irrelevant',
              'do_name_scan', 'do_ocr', 'do_address_scan',
              'do_link_check', 'do_external_link_check', 'do_collect_cookies',
              'do_last_modified_check', 'do_last_modified_check_head_request',
              'regex_rules', 'recipients']

    def get_form(self, form_class):
        """Get the form for the view.

        Querysets used for choices in the 'domains' and 'regex_rules' fields
        will be limited by the user's organiztion unless the user is a
        superuser.
        """
        form = super(ScannerCreate, self).get_form(form_class)
        try:
            organization = self.request.user.profile.organization
            groups = self.request.user.profile.groups.all()
        except UserProfile.DoesNotExist:
            organization = None
            groups = None

        # Exclude recipients with no email address
        form.fields[
            'recipients'
        ].queryset = form.fields[
            'recipients'
        ].queryset.exclude(user__email="")

        if not self.request.user.is_superuser:
            for field_name in ['domains', 'regex_rules', 'recipients']:
                queryset = form.fields[field_name].queryset
                queryset = queryset.filter(organization=organization)
                if (
                    self.request.user.profile.is_group_admin or
                    field_name == 'recipients'
                ):
                    # Already filtered by organization, nothing more to do.
                    pass
                else:
                    queryset = queryset.filter(
                        Q(group__in=groups) | Q(group__isnull=True)
                    )
                form.fields[field_name].queryset = queryset
        return form

    def get_success_url(self):
        """The URL to redirect to after successful creation."""
        return '/scanners/%s/created/' % self.object.pk


class ScannerUpdate(RestrictedUpdateView):

    """Update a scanner view."""

    model = Scanner
    fields = ['name', 'schedule', 'domains',
              'do_cpr_scan', 'do_cpr_modulus11', 'do_cpr_ignore_irrelevant',
              'do_name_scan', 'do_ocr', 'do_address_scan',
              'do_link_check', 'do_external_link_check', 'do_collect_cookies',
              'do_last_modified_check', 'do_last_modified_check_head_request',
              'regex_rules', 'recipients']

    def get_success_url(self):
        """The URL to redirect to after successful update."""
        return '/scanners/%s/saved/' % self.object.pk

    def get_form(self, form_class):
        """Get the form for the view.

        Querysets used for choices in the 'domains' and 'regex_rules' fields
        will be limited by the user's organiztion unless the user is a
        superuser.
        """
        self.fields = self.get_form_fields()
        form = super(ScannerUpdate, self).get_form(form_class)

        scanner = self.get_object()

        # Exclude recipients with no email address
        form.fields[
            'recipients'
        ].queryset = form.fields[
            'recipients'
        ].queryset.exclude(user__email="")

        for field_name in ['domains', 'regex_rules', 'recipients']:
            queryset = form.fields[field_name].queryset
            queryset = queryset.filter(organization=scanner.organization)

            if scanner.organization.do_use_groups:
                # TODO: This is not very elegant!
                if field_name == 'recipients':
                    if scanner.group:
                        queryset = queryset.filter(
                            Q(groups__in=scanner.group) |
                            Q(groups__isnull=True)
                        )
                else:
                    queryset = queryset.filter(
                        Q(group=scanner.group) | Q(group__isnull=True)
                    )
            form.fields[field_name].queryset = queryset
        return form


class ScannerDelete(RestrictedDeleteView):

    """Delete a scanner view."""

    model = Scanner
    success_url = '/scanners/'


class ScannerAskRun(RestrictedDetailView):

    """Prompt for starting scan, validate first."""
    model = Scanner

    def get_context_data(self, **kwargs):
        """Check that user is allowed to run this scanner."""
        context = super(ScannerAskRun, self).get_context_data(**kwargs)

        if self.object.has_active_scans:
            ok = False
            error_message = Scanner.ALREADY_RUNNING
        elif not self.object.has_valid_domains:
            ok = False
            error_message = Scanner.NO_VALID_DOMAINS
        else:
            ok = True
        context['ok'] = ok
        if not ok:
            context['error_message'] = error_message

        return context


class ScannerRun(RestrictedDetailView):

    """View that handles starting of a scanner run."""

    model = Scanner
    template_name = 'os2webscanner/scanner_run.html'

    def get(self, request, *args, **kwargs):
        """Handle a get request to the view."""
        self.object = self.get_object()

        result = self.object.run(user=request.user)
        context = self.get_context_data(object=self.object)
        context['success'] = isinstance(result, Scan)
        if not context['success']:
            context['error_message'] = result
        else:
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

    def get_form_fields(self):
        """Get the list of form fields."""
        fields = super(DomainUpdate, self).get_form_fields()

        if self.request.user.is_superuser:
            fields.append('validation_status')
        elif not self.object.validation_status:
            fields.append('validation_method')

        self.fields = fields
        return fields

    def get_form(self, form_class):
        """Get the form for the view.
        """
        form = super(DomainUpdate, self).get_form(form_class)

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
            user_profile = self.request.user.profile
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


class GroupCreate(RestrictedCreateView):

    """Create a group view."""

    fields = ['name', 'contact_email', 'contact_phone', 'user_profiles']
    model = Group

    def get_form_fields(self):
        """Get the list of fields to use in the form for the view."""
        fields = super(GroupCreate, self).get_form_fields()

        if 'group' in fields:
            fields.remove('group')

        return fields

    def get_form(self, form_class):
        """Get the form for the view.

        Querysets used for choices in the 'domains' and 'regex_rules' fields
        will be limited by the user's organiztion unless the user is a
        superuser.
        """
        form = super(GroupCreate, self).get_form(form_class)

        field_name = 'user_profiles'
        queryset = form.fields[field_name].queryset
        queryset = queryset.filter(organization=0)
        form.fields[field_name].queryset = queryset

        return form

    def get_success_url(self):
        """The URL to redirect to after successful creation."""
        return '/groups/%s/created/' % self.object.pk


class GroupUpdate(RestrictedUpdateView):

    """Update a domain view."""

    model = Group
    fields = ['name', 'contact_email', 'contact_phone', 'user_profiles']

    def get_form(self, form_class):
        """Get the form for the view.

        Querysets used for choices in the 'domains' and 'regex_rules' fields
        will be limited by the user's organiztion unless the user is a
        superuser.
        """
        form = super(GroupUpdate, self).get_form(form_class)
        group = self.get_object()
        field_name = 'user_profiles'
        queryset = form.fields[field_name].queryset
        if group.organization:
            queryset = queryset.filter(organization=group.organization)
        else:
            queryset = queryset.filter(organization=0)
        form.fields[field_name].queryset = queryset
        return form

    def get_success_url(self):
        """The URL to redirect to after successful update."""
        return '/groups/%s/saved/' % self.object.pk


class GroupDelete(RestrictedDeleteView):

    """Delete a domain view."""

    model = Group
    fields = ['name', 'contact_email', 'contact_phone', 'user_profiles']
    success_url = '/groups/'


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
    fields = ['name', 'match_string', 'description', 'sensitivity']

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
    fields = ['name', 'match_string', 'description', 'sensitivity']
    success_url = '/rules/'


# Reports stuff
class ReportDetails(UpdateView, LoginRequiredMixin):

    """Display a detailed report summary."""

    model = Scan
    template_name = 'os2webscanner/report.html'
    context_object_name = "scan"
    full = False

    fields = '__all__'

    def get_queryset(self):
        """Get the queryset for the view.

        If the user is not a superuser the queryset will be limited by the
        user's organization.
        """
        queryset = super(ReportDetails, self).get_queryset()
        if not self.request.user.is_superuser:
            try:
                user_profile = self.request.user.profile
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

        referrer_urls = ReferrerUrl.objects.filter(scan=self.get_object())

        context['full_report'] = self.full
        context['broken_urls'] = broken_urls
        context['no_of_broken_links'] = broken_urls.count()
        context['referrer_urls'] = referrer_urls
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
                user_profile = self.request.user.profile
                organization = user_profile.organization
            except UserProfile.DoesNotExist:
                organization = None
            queryset = queryset.filter(scanner__organization=organization)
        return queryset


class ScanReportLog(ReportDetails):

    """Display ordinary log file for debugging purposes."""

    def render_to_response(self, context, **response_kwargs):
        """Render log file."""
        scan = self.get_object()
        response = HttpResponse(content_type="text/plain")
        log_file = "scan{0}_log.txt".format(scan.id)
        response[
            'Content-Disposition'
        ] = u'attachment; filename={0}'.format(log_file)

        with open(scan.scan_log_file, "r") as f:
            response.write(f.read())
        return response


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
        def e(fields):
            return ([f.encode('utf-8') for f in fields])

        # Print summary header
        writer.writerow(e([u'Starttidspunkt', u'Sluttidspunkt', u'Status',
                        u'Totalt antal matches', u'Total antal broken links']))
        # Print summary
        writer.writerow(
            e(
                [str(scan.start_time),
                 str(scan.end_time), scan.get_status_display(),
                 str(context['no_of_matches']),
                 str(context['no_of_broken_links'])]
            )
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
                    writer.writerow(
                        e([referrer.url,
                           url.url,
                           url.status_message])
                    )
        return response


class DialogSuccess(TemplateView):

    """View that handles success for iframe-based dialogs."""

    template_name = 'os2webscanner/dialogsuccess.html'

    type_map = {
        'domains': Domain,
        'scanners': Scanner,
        'rules': RegexRule,
        'groups': Group,
        'summaries': Summary,
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


class SystemStatusView(TemplateView, SuperUserRequiredMixin):

    """Display the system status for superusers."""

    template_name = 'os2webscanner/system_status.html'

    def get_context_data(self, **kwargs):
        """Setup context for the template."""
        context = super(SystemStatusView, self).get_context_data(**kwargs)
        all = ConversionQueueItem.objects.filter(
            status=ConversionQueueItem.NEW
        )
        total = all.count()
        totals_by_type = all.values('type').annotate(
            total=Count('type')
        ).order_by('-total')
        totals_by_scan = all.values('url__scan__pk').annotate(
            total=Count('url__scan__pk')
        ).order_by('-total')
        totals_by_scan_and_type = all.values('url__scan__pk', 'type').annotate(
            total=Count('type')
        ).order_by('-total')

        for item in totals_by_scan:
            item['scan'] = Scan.objects.get(pk=item['url__scan__pk'])
            by_type = []
            for x in totals_by_scan_and_type:
                if x['url__scan__pk'] == item['url__scan__pk']:
                    by_type.append({
                        'total': x['total'],
                        'type': x['type']
                    })
            item['by_type'] = by_type

        def assign_percentages(grouped_totals, total):
            for item in grouped_totals:
                item['percentage'] = "%.1f" % (float(item['total']) /
                                               total * 100.)

        assign_percentages(totals_by_type, total)
        assign_percentages(totals_by_scan, total)

        context['total_queue_items'] = total
        context['total_queue_items_by_type'] = totals_by_type
        context['total_queue_items_by_scan'] = totals_by_scan
        return context


class SummaryList(RestrictedListView):

    """Displays list of summaries."""

    model = Summary
    template_name = 'os2webscanner/summaries.html'


class SummaryCreate(RestrictedCreateView):

    """Create new summary."""

    model = Summary
    fields = ['name', 'description', 'schedule', 'last_run', 'recipients',
              'scanners']

    def get_form(self, form_class):
        """Set up fields and return form."""
        form = super(SummaryCreate, self).get_form(form_class)

        field_names = ['recipients', 'scanners']
        for field_name in field_names:
            queryset = form.fields[field_name].queryset
            queryset = queryset.filter(organization=0)
            form.fields[field_name].queryset = queryset

        return form

    def get_success_url(self):
        """The URL to redirect to after successful creation."""
        return '/summaries/{0}/created/'.format(self.object.id)


class SummaryUpdate(RestrictedUpdateView):

    """Edit summary."""

    model = Summary
    fields = ['name', 'description', 'schedule', 'last_run', 'recipients',
              'scanners', 'do_email_recipients']

    def get_form(self, form_class):
        """Get the form for the view.

        Querysets for selecting the field 'recipients' must be limited by the
        summary's organization - i.e., there must be an organization set on
        the object.
        """
        form = super(SummaryUpdate, self).get_form(form_class)
        summary = self.get_object()
        # Limit recipients to organization
        queryset = form.fields['recipients'].queryset
        if summary.organization:
            queryset = queryset.filter(organization=summary.organization)
        else:
            queryset = queryset.filter(organization=0)
        form.fields['recipients'].queryset = queryset

        # Limit scanners to organization
        queryset = form.fields['scanners'].queryset
        if summary.organization:
            queryset = queryset.filter(organization=summary.organization)
        else:
            queryset = queryset.filter(organization=0)

        # Only display visible scanners
        queryset = queryset.filter(is_visible=True)
        form.fields['scanners'].queryset = queryset

        return form

    def get_success_url(self):
        """The URL to redirect to after successful update."""
        return '/summaries/%s/saved/' % self.object.pk


class SummaryDelete(RestrictedDeleteView):

    """Delete summary."""

    model = Summary
    success_url = '/summaries/'


class SummaryReport(RestrictedDetailView):

    """Display report for summary."""

    model = Summary
    template_name = 'os2webscanner/summary_report.html'

    def get_context_data(self, **kwargs):
        """Setup context for the template."""
        context = super(SummaryReport, self).get_context_data(**kwargs)

        summary = self.object
        scan_list, from_date, to_date = scans_for_summary_report(summary)

        context['scans'] = scan_list
        context['from_date'] = from_date
        context['to_date'] = to_date

        return context

@login_required
def referrer_content(request, pk):
    u = ReferrerUrl.objects.get(id=int(pk))
    return HttpResponse(u.content)

@login_required
def file_upload(request):
    """Handle upload of file for scanning."""
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Perform the scan
            upload_file = request.FILES['scan_file']
            extension = upload_file.name.split('.')[-1]
            # Get parametes
            params = {}
            params['do_cpr_scan'] = form.cleaned_data['do_cpr_scan']
            params['do_cpr_replace'] = form.cleaned_data['do_replace_cpr']
            params['cpr_replace_text'] = form.cleaned_data[
                'cpr_replacement_text'
            ]
            params['do_name_scan'] = form.cleaned_data['do_name_scan']
            params['do_name_replace'] = form.cleaned_data['do_replace_name']
            params['name_replace_text'] = form.cleaned_data[
                'name_replacement_text'
            ]
            params['do_address_scan'] = form.cleaned_data['do_address_scan']
            params['do_address_replace'] = form.cleaned_data[
                'do_replace_address'
            ]
            params['do_ocr'] = form.cleaned_data['do_ocr']
            params['address_replace_text'] = form.cleaned_data[
                'address_replacement_text'
            ]
            params['output_spreadsheet_file'] = (extension != 'pdf')

            def to_int(L):
                return str(ord(L) - ord('A') + 1) if L else ''
            params['columns'] = ','.join(
                map(to_int, form.cleaned_data['column_list'].split(','))
            )

            path = upload_file.temporary_file_path()
            rpcdir = settings.RPC_TMP_PREFIX
            try:
                os.makedirs(rpcdir)
            except OSError:
                if os.path.isdir(rpcdir):
                    pass
                else:
                    # There was an error, so make sure we know about it
                    raise
            # Now create temporary dir, fill with files
            dirname = tempfile.mkdtemp(dir=rpcdir)
            file_path = os.path.join(dirname,
                                     upload_file.name).encode('utf-8')
            copyfile(path, file_path)
            file_url = 'file://{0}'.format(file_path)
            scan = do_scan(request.user, [file_url], params, blocking=True,
                           visible=True)
            scan.scanner.is_visible = False
            scan.scanner.save()

            #
            if not isinstance(scan, Scan):
                raise RuntimeError("Unable to perform scan - check user has"
                                   "organization and valid domain")
            # We now have the scan object
            if not params['output_spreadsheet_file']:
                return HttpResponseRedirect('/report/{0}/'.format(scan.pk))
            response = HttpResponse(content_type='text/csv')
            report_file = u'{0}{1}.csv'.format(
                scan.scanner.organization.name.replace(u' ', u'_'),
                scan.id)
            response[
                'Content-Disposition'
            ] = u'attachment; filename={0}'.format(report_file)
            csv_file = open(scan.scan_output_file, "rb")

            # Load CSV file, write it back to the client
            response.write(codecs.BOM_UTF8)
            csv_data = csv_file.read()
            response.write(csv_data)

            return response

    else:
        # Request.method == 'GET'
        form = FileUploadForm()

    return render_to_response(
        'os2webscanner/file_upload.html',
        RequestContext(request, {'form': form})
    )
