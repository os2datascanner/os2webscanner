from ..models.domains.domain_model import Domain
from ..models.domains.webdomain_model import WebDomain
from ..validate import get_validation_str, validate_domain
from .domain_views import DomainList, DomainCreate, DomainUpdate
from .views import RestrictedDeleteView, RestrictedDetailView


class WebDomainList(DomainList):

    """Displays list of domains."""

    model = WebDomain
    type = 'web'


class WebDomainCreate(DomainCreate):

    """Web domain create form."""

    model = WebDomain
    fields = ['url', 'exclusion_rules', 'download_sitemap', 'sitemap_url',
              'sitemap']

    def get_success_url(self):
        """The URL to redirect to after successful creation."""
        return '/webdomains/%s/created/' % self.object.pk


class WebDomainUpdate(DomainUpdate):
    """Update a web domain view."""

    model = WebDomain
    fields = ['url', 'exclusion_rules', 'download_sitemap',
              'sitemap_url', 'sitemap']

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
        for value, desc in WebDomain.validation_method_choices:
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
            return '/webdomains/%s/saved/' % self.object.pk


class WebDomainDelete(RestrictedDeleteView):

    """Delete a domain view."""

    model = Domain
    success_url = '/webdomains/'

class WebDomainValidate(RestrictedDetailView):

    """View that handles validation of a domain."""

    model = WebDomain

    def get_context_data(self, **kwargs):
        """Perform validation and populate the template context."""
        context = super().get_context_data(**kwargs)
        context['validation_status'] = self.object.validation_status
        if not self.object.validation_status:
            result = validate_domain(self.object)

            if result:
                self.object.validation_status = Domain.VALID
                self.object.save()

            context['validation_success'] = result

        return context
