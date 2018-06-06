from django.db.models import Count, Q

from .views import RestrictedListView, RestrictedCreateView, \
    RestrictedUpdateView, RestrictedDetailView, RestrictedDeleteView

from ..models.scan_model import Scan
from ..models.scanner_model import Scanner
from ..models.webscanner_model import WebScanner
from ..models.filescanner_model import FileScanner
from ..models.userprofile_model import UserProfile


class ScannerList(RestrictedListView):

    """Displays list of scanners."""

    template_name = 'os2webscanner/scanners.html'
    context_object_name = 'scanner_list'

    def get_queryset(self):
        """Get queryset, don't include non-visible scanners."""
        qs = super().get_queryset()
        # Dismiss scans that are not visible
        qs = qs.filter(is_visible=True)
        return qs


class WebScannerList(ScannerList):

    """Displays list of web scanners."""

    model = WebScanner
    type = 'web'


class FileScannerList(ScannerList):

    """Displays list of file scanners."""

    model = FileScanner
    type = 'file'


class ScannerCreate(RestrictedCreateView):

    template_name = 'os2webscanner/scanner_form.html'

    def get_form(self, form_class=None):
        """Get the form for the view.

        Querysets used for choices in the 'domains' and 'regex_rules' fields
        will be limited by the user's organization unless the user is a
        superuser.
        """
        if form_class is None:
            form_class = self.get_form_class()

        form = super().get_form(form_class)
        form.fields['schedule'].required = False
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


class WebScannerCreate(ScannerCreate):

    """Web scanner create form."""

    model = WebScanner
    fields = ['name', 'schedule', 'domains',
              'do_cpr_scan', 'do_cpr_modulus11', 'do_cpr_ignore_irrelevant',
              'do_name_scan', 'do_ocr', 'do_address_scan',
              'do_link_check', 'do_external_link_check', 'do_collect_cookies',
              'do_last_modified_check', 'do_last_modified_check_head_request',
              'regex_rules', 'recipients']

    def get_success_url(self):
        """The URL to redirect to after successful creation."""
        return '/webscanners/%s/created/' % self.object.pk


class FileScannerCreate(ScannerCreate):

    """Create a file scanner view."""

    model = FileScanner
    fields = ['name', 'schedule', 'domains',
              'do_cpr_scan', 'do_cpr_modulus11', 'do_cpr_ignore_irrelevant',
              'do_name_scan', 'do_ocr', 'do_address_scan', 'do_last_modified_check',
              'regex_rules', 'recipients']

    def get_success_url(self):
        """The URL to redirect to after successful creation."""
        return '/filescanners/%s/created/' % self.object.pk


class ScannerUpdate(RestrictedUpdateView):

    """Update a scanner view."""
    template_name = 'os2webscanner/scanner_form.html'

    def get_form(self, form_class=None):
        """Get the form for the view.

        Querysets used for choices in the 'domains' and 'regex_rules' fields
        will be limited by the user's organiztion unless the user is a
        superuser.
        """
        if form_class is None:
            form_class = self.get_form_class()

        self.fields = self.get_form_fields()
        form = super().get_form(form_class)
        form.fields['schedule'].required = False

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


class WebScannerUpdate(ScannerUpdate):

    """Update a scanner view."""

    model = WebScanner
    fields = ['name', 'schedule', 'domains',
              'do_cpr_scan', 'do_cpr_modulus11', 'do_cpr_ignore_irrelevant',
              'do_name_scan', 'do_ocr', 'do_address_scan',
              'do_link_check', 'do_external_link_check', 'do_collect_cookies',
              'do_last_modified_check', 'do_last_modified_check_head_request',
              'regex_rules', 'recipients']

    def get_success_url(self):
        """The URL to redirect to after successful update."""
        return '/webscanners/%s/saved/' % self.object.pk


class FileScannerUpdate(ScannerUpdate):

    """Update a scanner view."""

    model = FileScanner
    fields = ['name', 'schedule', 'domains',
              'do_cpr_scan', 'do_cpr_modulus11', 'do_cpr_ignore_irrelevant',
              'do_name_scan', 'do_ocr', 'do_address_scan', 'do_last_modified_check',
              'regex_rules', 'recipients']


    def get_success_url(self):
        """The URL to redirect to after successful update."""
        return '/filescanners/%s/saved/' % self.object.pk


class ScannerDelete(RestrictedDeleteView):

    """Delete a scanner view."""
    template_name = 'os2webscanner/scanner_confirm_delete.html'

    def get_form(self, form_class=None):
        """Adds special field password and decrypts password."""
        if form_class is None:
            form_class = self.get_form_class()
        form = super().get_form(form_class)

        return form

class WebScannerDelete(ScannerDelete):
    """Delete a scanner view."""
    model = WebScanner
    fields = []
    success_url = '/webscanners/'


class FileScannerDelete(ScannerDelete):
    """Delete a scanner view."""
    model = FileScanner
    fields = []
    success_url = '/filescanners/'


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


class WebScannerAskRun(ScannerAskRun):

    """Prompt for starting web scan, validate first."""

    model = WebScanner


class FileScannerAskRun(ScannerAskRun):

    """Prompt for starting file scan, validate first."""

    model = FileScanner


class ScannerRun(RestrictedDetailView):

    """Base class for view that handles starting of a scanner run."""

    template_name = 'os2webscanner/scanner_run.html'
    model = Scanner

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


class WebScannerRun(ScannerRun):

    """View that handles starting of a web scanner run."""

    model = WebScanner


class FileScannerRun(ScannerRun):

    """View that handles starting of a file scanner run."""

    model = FileScanner
