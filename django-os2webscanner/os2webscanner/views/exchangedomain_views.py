from django import forms

from ..models.domain_model import Domain
from ..models.exchangedomain_model import ExchangeDomain

from .domain_views import DomainList, DomainCreate, DomainUpdate
from .views import RestrictedDeleteView

from ..aescipher import decrypt


class ExchangeDomainList(DomainList):

    """Displays list of domains."""

    model = ExchangeDomain
    type = 'exchange'


class ExchangeDomainCreate(DomainCreate):

    """File domain create form."""

    model = ExchangeDomain
    fields = ['url', 'userlist']

    def get_form(self, form_class=None):
        """Adds special field password."""
        if form_class is None:
            form_class = self.get_form_class()

        form = super().get_form(form_class)
        form.fields['username'] = forms.CharField(max_length=1024, required=False)
        form.fields['password'] = forms.CharField(max_length=50, required=False)
        return form

    def form_valid(self, form):
        """Makes sure password gets encrypted before stored in db."""
        return super().form_valid(form)

    def get_success_url(self):
        """The URL to redirect to after successful creation."""
        return '/exchangedomains/%s/created/' % self.object.pk


class ExchangeDomainUpdate(DomainUpdate):
    """Update a file domain view."""

    model = ExchangeDomain
    fields = ['url', 'userlist']

    def get_form(self, form_class=None):
        """Adds special field password and decrypts password."""
        if form_class is None:
            form_class = self.get_form_class()

        form = super().get_form(form_class)
        exchangedomain = self.get_object()
        authentication = exchangedomain.authentication
        form.fields['username'] = forms.CharField(max_length=1024, required=False)
        form.fields['password'] = forms.CharField(max_length=50, required=False)
        if len(authentication.username) > 0:
            form.fields['username'].initial = authentication.username
        if len(authentication.ciphertext) > 0:
            password = decrypt(bytes(authentication.iv),
                               bytes(authentication.ciphertext))
            form.fields['password'].initial = password
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
            return '/exchangedomains/%s/saved/' % self.object.pk


class ExchangeDomainDelete(RestrictedDeleteView):

    """Delete a domain view."""

    model = Domain
    success_url = '/exchangedomains/'
