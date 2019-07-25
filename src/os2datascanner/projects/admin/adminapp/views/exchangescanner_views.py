from django import forms

from .scanner_views import *
from ..models.scannerjobs.exchangescanner_model import ExchangeScanner


class ExchangeScannerList(ScannerList):
    """Displays list of exchange scanners."""

    model = ExchangeScanner
    type = 'exchange'


class ExchangeScannerCreate(ScannerCreate):
    """Create a exchange scanner view."""

    model = ExchangeScanner
    fields = ['name', 'schedule', 'do_ocr',
              'do_last_modified_check', 'rules', 'recipients']

    def get_success_url(self):
        """The URL to redirect to after successful creation."""
        return '/exchangescanners/%s/created/' % self.object.pk

    def get_form(self, form_class=None):
        """Adds special field password."""
        if form_class is None:
            form_class = self.get_form_class()

        form = super().get_form(form_class)
        form.fields['username'] = forms.CharField(max_length=1024, required=False)
        form.fields['password'] = forms.CharField(max_length=50, required=False)
        return form

class ExchangeScannerUpdate(ScannerUpdate):
    """Update a scanner view."""

    model = ExchangeScanner
    fields = ['name', 'schedule', 'do_ocr', 'do_last_modified_check',
              'rules', 'recipients', 'url', 'userlist']

    def get_success_url(self):
        """The URL to redirect to after successful updating.

        Will redirect the user to the validate view if the form was submitted
        with the 'save_and_validate' button.
        """
        if 'save_and_validate' in self.request.POST:
            return 'validate/'
        else:
            return '/exchangescanners/%s/saved/' % self.object.pk

    def get_form(self, form_class=None):
        """Adds special field password and decrypts password."""
        if form_class is None:
            form_class = self.get_form_class()

        form = super().get_form(form_class)
        exchangedomain = self.get_object()
        authentication = exchangedomain.authentication
        form.fields['username'] = forms.CharField(max_length=1024, required=False)
        form.fields['password'] = forms.CharField(max_length=50, required=False)
        if authentication.username:
            form.fields['username'].initial = authentication.username
        if authentication.ciphertext:
            password = decrypt(bytes(authentication.iv),
                               bytes(authentication.ciphertext))
            form.fields['password'].initial = password
        return form


class ExchangeScannerDelete(ScannerDelete):
    """Delete a scanner view."""
    model = ExchangeScanner
    fields = []
    success_url = '/exchangescanners/'


class ExchangeScannerAskRun(ScannerAskRun):
    """Prompt for starting exchange scan, validate first."""

    model = ExchangeScanner

    def get_context_data(self, **kwargs):
        """Check that user is allowed to run this scanner."""
        context = super().get_context_data(**kwargs)

        if not self.object.is_ready_to_scan:
            ok = False
            error_message = Scanner.EXCHANGE_EXPORT_IS_RUNNING
        else:
            ok = True

        context['ok'] = ok
        if not ok:
            context['error_message'] = error_message

        return context


class ExchangeScannerRun(ScannerRun):
    """View that handles starting of a exchange scanner run."""

    model = ExchangeScanner
