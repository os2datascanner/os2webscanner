from django import forms

from .domain_views import DomainList, DomainCreate, DomainUpdate

from ..models.domain_model import Domain
from ..models.filedomain_model import FileDomain
from .views import RestrictedDeleteView
from ..aescipher import decrypt


class FileDomainList(DomainList):

    """Displays list of domains."""

    model = FileDomain
    type = 'file'


class FileDomainCreate(DomainCreate):

    """File domain create form."""

    model = FileDomain
    fields = ['url', 'exclusion_rules']

    def get_form(self, form_class=None):
        """Adds special field password."""
        if form_class is None:
            form_class = self.get_form_class()

        form = super().get_form(form_class)
        form.fields['username'] = forms.CharField(max_length=1024, required=False)
        form.fields['password'] = forms.CharField(max_length=50, required=False)
        form.fields['domain'] = forms.CharField(max_length=2024, required=False)
        return form

    def form_valid(self, form):
        """Makes sure password gets encrypted before stored in db."""
        return super().form_valid(form)

    def get_success_url(self):
        """The URL to redirect to after successful creation."""
        return '/filedomains/%s/created/' % self.object.pk


class FileDomainUpdate(DomainUpdate):
    """Update a file domain view."""

    model = FileDomain
    fields = ['url', 'exclusion_rules']

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
        if len(authentication.username) > 0:
            form.fields['username'].initial = authentication.username
        if len(authentication.ciphertext) > 0:
            password = decrypt(bytes(authentication.iv),
                               bytes(authentication.ciphertext))
            form.fields['password'].initial = password
        if len(authentication.domain) > 0:
            form.fields['domain'].initial = authentication.domain
        return form

    def form_valid(self, form):
        """Makes sure password gets encrypted before stored in db."""
        return super().form_valid(form)

    def get_success_url(self):
        """The URL to redirect to after successful updating.

        Will redirect the user to the validate view if the form was submitted
        with the 'save_and_validate' button.
        """
        if 'save_and_validate' in self.request.POST:
            return 'validate/'
        else:
            return '/filedomains/%s/saved/' % self.object.pk


class FileDomainDelete(RestrictedDeleteView):

    """Delete a domain view."""

    model = Domain
    success_url = '/filedomains/'
