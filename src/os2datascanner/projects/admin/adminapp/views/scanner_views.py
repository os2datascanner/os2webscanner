from django.db.models import Q

from .views import RestrictedListView, RestrictedCreateView, \
    RestrictedUpdateView, RestrictedDetailView, RestrictedDeleteView
from ..models.scans.scan_model import Scan
from ..models.scannerjobs.scanner_model import Scanner
from ..models.userprofile_model import UserProfile


class ScannerList(RestrictedListView):
    """Displays list of scanners."""

    template_name = 'os2datascanner/scanners.html'
    context_object_name = 'scanner_list'

    def get_queryset(self):
        """Get queryset, don't include non-visible scanners."""
        qs = super().get_queryset()
        # Dismiss scans that are not visible
        qs = qs.filter(is_visible=True)
        return qs


class ScannerBase():
    template_name = 'os2datascanner/scanner_form.html'

    def get_form(self, form_class=None):

        if form_class is None:
            form_class = self.get_form_class()

        form = super().get_form(form_class)
        form.fields['schedule'].required = False

        # Exclude recipients with no email address
        form.fields[
            'recipients'
        ].queryset = form.fields[
            'recipients'
        ].queryset.exclude(user__email="")

        return form

    def get_scanner_object(self):
        return self.get_object()


class ScannerCreate(ScannerBase, RestrictedCreateView):
    """View for creating a new scannerjob."""

    def get_form(self, form_class=None):
        """Get the form for the view.

        Querysets used for choices in the 'domains' and 'regex_rules' fields
        will be limited by the user's organization unless the user is a
        superuser.
        """
        form = super().get_form(form_class)
        try:
            organization = self.request.user.profile.organization
            groups = self.request.user.profile.groups.all()
        except UserProfile.DoesNotExist:
            organization = None
            groups = None

        if not self.request.user.is_superuser:
            self.filter_queryset(form, groups, organization)

        return form

    def filter_queryset(self, form, groups, organization):
        for field_name in ['domains', 'regex_rules', 'recipients']:
            queryset = form.fields[field_name].queryset
            queryset = queryset.filter(organization=organization)
            if (self.request.user.profile.is_group_admin or
                            field_name == 'recipients'):
                # Already filtered by organization, nothing more to do.
                pass
            else:
                queryset = queryset.filter(
                    Q(group__in=groups) | Q(group__isnull=True)
                )
            form.fields[field_name].queryset = queryset


class ScannerUpdate(ScannerBase, RestrictedUpdateView):
    """View for editing an existing scannerjob."""
    edit = True

    editable_fields = (
        'name',
        'organisation',
        'recipients',
        'schedule',
    )

    def get_form(self, form_class=None):
        """Get the form for the view.

        Querysets used for choices in the 'domains' and 'regex_rules' fields
        will be limited by the user's organization unless the user is a
        superuser.
        """
        form = super().get_form(form_class)

        for field_name, field in form.fields.items():
            if field_name not in self.editable_fields:
                form.fields[field_name].disabled = True

        scanner = self.get_scanner_object()

        self.filter_queryset(form, scanner)

        return form

    def filter_queryset(self, form, scanner):
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


class ScannerDelete(RestrictedDeleteView):
    """Delete a scanner view."""
    template_name = 'os2datascanner/scanner_confirm_delete.html'

    def get_form(self, form_class=None):
        """Adds special field password and decrypts password."""
        if form_class is None:
            form_class = self.get_form_class()
        form = super().get_form(form_class)

        return form


class ScannerAskRun(RestrictedDetailView):
    """Base class for prompt before starting scan, validate first."""
    fields = []

    def get_context_data(self, **kwargs):
        """Check that user is allowed to run this scanner."""
        context = super().get_context_data(**kwargs)

        if self.object.is_running:
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

    """Base class for view that handles starting of a scanner run."""

    template_name = 'os2datascanner/scanner_run.html'
    model = Scanner

    def __init__(self):
        self.object = None

    def get(self, request, *args, **kwargs):
        """Handle a get request to the view."""
        self.object = self.get_object()
        result = self.object.run(type(self.object).__name__,
                                 user=request.user)

        context = self.get_context_data(object=self.object)
        context['success'] = isinstance(result, Scan)

        if not context['success']:
            context['error_message'] = result
        else:
            context['scan'] = result

        return self.render_to_response(context)



