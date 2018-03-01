from django import forms
from django.db.models import Count, Q

from views import RestrictedListView, RestrictedCreateView, \
    RestrictedUpdateView, RestrictedDetailView, RestrictedDeleteView

from ..models.scan_model import Scan
from ..models.scanner_model import Scanner
from ..models.webscanner_model import WebScanner
from ..models.filescanner_model import FileScanner
from ..models.userprofile_model import UserProfile
from ..aescipher import encrypt, decrypt


class ScannerList(RestrictedListView):

    """Displays list of scanners."""

    template_name = 'os2webscanner/scanners.html'
    context_object_name = 'scanner_list'

    def get_queryset(self):
        """Get queryset, don't include non-visible scanners."""
        qs = super(ScannerList, self).get_queryset()
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

    def get_form(self, form_class):
        """Get the form for the view.

        Querysets used for choices in the 'domains' and 'regex_rules' fields
        will be limited by the user's organization unless the user is a
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
    fields = ['name', 'schedule', 'domains', 'username',
              'do_cpr_scan', 'do_cpr_modulus11', 'do_cpr_ignore_irrelevant',
              'do_name_scan', 'do_ocr', 'do_address_scan', 'do_last_modified_check',
              'regex_rules', 'recipients']

    def get_form(self, form_class):
        """Adds special field password."""
        form = super(FileScannerCreate, self).get_form(form_class)
        form.fields['password'] = forms.CharField(max_length=50)
        return form

    def form_valid(self, form):
        """Makes sure password gets encrypted before stored in db."""
        filescanner = form.save(commit=False)
        if len(form.cleaned_data['password']) > 0:
            iv, ciphertext = encrypt(str(form.cleaned_data['password']))
            filescanner.ciphertext = ciphertext
            filescanner.iv = iv
        filescanner.save()
        return super(FileScannerCreate, self).form_valid(form)

    def get_success_url(self):
        """The URL to redirect to after successful creation."""
        return '/filescanners/%s/created/' % self.object.pk


class ScannerUpdate(RestrictedUpdateView):

    """Update a scanner view."""
    template_name = 'os2webscanner/scanner_form.html'

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
    fields = ['name', 'schedule', 'domains', 'username',
              'do_cpr_scan', 'do_cpr_modulus11', 'do_cpr_ignore_irrelevant',
              'do_name_scan', 'do_ocr', 'do_address_scan', 'do_last_modified_check',
              'regex_rules', 'recipients']

    def get_form(self, form_class):
        """Adds special field password and decrypts password."""
        form = super(FileScannerUpdate, self).get_form(form_class)
        scanner = self.get_object()
        form.fields['password'] = forms.CharField(max_length=50)
        if len(scanner.ciphertext) > 0:
            password = decrypt(str(scanner.iv), str(scanner.ciphertext))
            form.fields['password'].initial = password
        return form

    def get_success_url(self):
        """The URL to redirect to after successful update."""
        return '/filescanners/%s/saved/' % self.object.pk


class ScannerDelete(RestrictedDeleteView):

    """Delete a scanner view."""

    model = WebScanner
    success_url = '/webscanners/'


class ScannerAskRun(RestrictedDetailView):

    """Base class for prompt before starting scan, validate first."""

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


class WebScannerAskRun(ScannerAskRun):

    """Prompt for starting web scan, validate first."""

    model = WebScanner


class FileScannerAskRun(ScannerAskRun):

    """Prompt for starting file scan, validate first."""

    model = FileScanner


class ScannerRun(RestrictedDetailView):

    """Base class for view that handles starting of a scanner run."""

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


class WebScannerRun(ScannerRun):

    """View that handles starting of a web scanner run."""

    model = WebScanner


class FileScannerRun(ScannerRun):

    """View that handles starting of a file scanner run."""

    model = FileScanner