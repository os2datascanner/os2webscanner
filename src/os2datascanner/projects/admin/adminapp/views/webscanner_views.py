from ..validate import validate_domain, get_validation_str
from .scanner_views import *
from ..models.scannerjobs.webscanner_model import WebScanner


def url_contains_spaces(form):
    return form['url'].value() and ' ' in form['url'].value()


class WebScannerList(ScannerList):
    """Displays list of web scanners."""

    model = WebScanner
    type = 'web'


class WebScannerCreate(ScannerCreate):
    """Web scanner create form."""

    model = WebScanner
    type = 'web'
    fields = ['name', 'schedule', 'url', 'exclusion_rules',
              'download_sitemap', 'sitemap_url', 'sitemap', 'do_ocr',
              'do_link_check', 'do_external_link_check', 'do_collect_cookies',
              'do_last_modified_check', 'do_last_modified_check_head_request',
              'rules', 'recipients']

    def form_valid(self, form):
        if url_contains_spaces(form):
            form.add_error('url', u'Mellemrum er ikke tilladt i web-domænenavnet.')
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        """The URL to redirect to after successful creation."""
        return '/webscanners/%s/created/' % self.object.pk


class WebScannerUpdate(ScannerUpdate):
    """Update a scanner view."""

    model = WebScanner
    type = 'web'
    fields = ['name', 'schedule', 'url', 'exclusion_rules',
              'download_sitemap', 'sitemap_url', 'sitemap', 'do_ocr',
              'do_link_check', 'do_external_link_check', 'do_collect_cookies',
              'do_last_modified_check', 'do_last_modified_check_head_request',
              'rules', 'recipients']

    def form_valid(self, form):
        if url_contains_spaces(form):
            form.add_error('url', u'Mellemrum er ikke tilladt i web-domænenavnet.')
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_form_fields(self):
        fields = super().get_form_fields()
        if not self.request.user.is_superuser and \
                not self.object.validation_status:
            fields.append('validation_method')
        self.fields = fields
        return fields

    def get_context_data(self, **kwargs):
        """Get the context used when rendering the template."""
        context = super().get_context_data(**kwargs)
        for value, desc in WebScanner.validation_method_choices:
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
            return '/webscanners/%s/saved/' % self.object.pk


class WebScannerDelete(ScannerDelete):
    """Delete a scanner view."""
    model = WebScanner
    fields = []
    success_url = '/webscanners/'


class WebScannerAskRun(ScannerAskRun):
    """Prompt for starting web scan, validate first."""

    model = WebScanner


class WebScannerRun(ScannerRun):

    """View that handles starting of a web scanner run."""

    model = WebScanner


class WebScannerValidate(RestrictedDetailView):

    """View that handles validation of a domain."""

    model = WebScanner

    def get_context_data(self, **kwargs):
        """Perform validation and populate the template context."""
        context = super().get_context_data(**kwargs)
        context['validation_status'] = self.object.validation_status
        if not self.object.validation_status:
            result = validate_domain(self.object)

            if result:
                self.object.validation_status = self.model.VALID
                self.object.save()

            context['validation_success'] = result

        return context
