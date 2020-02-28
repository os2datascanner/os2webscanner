from django import forms
from .scanner_views import *
from ..aescipher import decrypt
from ..models.scannerjobs.filescanner_model import FileScanner


class FileScannerList(ScannerList):
    """Displays list of file scanners."""

    model = FileScanner
    type = 'file'


class FileScannerCreate(ScannerCreate):
    """Create a file scanner view."""

    model = FileScanner
    fields = [
        'name',
        'schedule',
        'url',
        'exclusion_rules',
        'alias',
        'do_ocr',
        'do_last_modified_check',
        'rules',
        'recipients'
        ]

    def get_form(self, form_class=None):
        """Adds special field password."""
        if form_class is None:
            form_class = self.get_form_class()

        form = super().get_form(form_class)
        form.fields['username'] = forms.CharField(max_length=1024, required=False)
        form.fields['password'] = forms.CharField(max_length=50, required=False)
        form.fields['domain'] = forms.CharField(max_length=2024, required=False)
        form.fields['alias'] = forms.CharField(max_length=64, required=False)
        return form

    def get_success_url(self):
        """The URL to redirect to after successful creation."""
        return '/filescanners/%s/created/' % self.object.pk


class FileScannerUpdate(ScannerUpdate):
    """Update a scanner view."""

    model = FileScanner
    fields = [
        'name',
        'schedule',
        'url',
        'exclusion_rules',
        'alias',
        'do_ocr',
        'do_last_modified_check',
        'rules',
        'recipients'
        ]

    def get_form(self, form_class=None):
        """Adds special field password and decrypts password."""
        if form_class is None:
            form_class = self.get_form_class()

        form = super().get_form(form_class)
        filedomain = self.get_object()
        authentication = filedomain.authentication
        form.fields['username'] = forms.CharField(max_length=1024, required=False)
        form.fields['password'] = forms.CharField(max_length=50, required=False)
        form.fields['domain'] = forms.CharField(max_length=2024, required=False)
        form.fields['alias'] = forms.CharField(max_length=64, required=False)
        if authentication.username:
            form.fields['username'].initial = authentication.username
        if authentication.ciphertext:
            password = decrypt(bytes(authentication.iv),
                               bytes(authentication.ciphertext))
            form.fields['password'].initial = password
        if authentication.domain:
            form.fields['domain'].initial = authentication.domain
        return form

    def get_success_url(self):
        """The URL to redirect to after successful updating.

        Will redirect the user to the validate view if the form was submitted
        with the 'save_and_validate' button.
        """
        if 'save_and_validate' in self.request.POST:
            return 'validate/'
        else:
            return '/filescanners/%s/saved/' % self.object.pk


class FileScannerDelete(ScannerDelete):
    """Delete a scanner view."""
    model = FileScanner
    fields = []
    success_url = '/filescanners/'


class FileScannerAskRun(ScannerAskRun):
    """Prompt for starting file scan, validate first."""

    model = FileScanner


class FileScannerRun(ScannerRun):
    """View that handles starting of a file scanner run."""

    model = FileScanner
