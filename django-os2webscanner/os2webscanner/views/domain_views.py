from django import forms

from .views import RestrictedListView, RestrictedCreateView, \
    RestrictedUpdateView, RestrictedDetailView
from ..models.authentication_model import Authentication
from ..models.domains.domain_model import Domain
from ..utils import domain_form_manipulate
from ..validate import validate_domain


class DomainList(RestrictedListView):

    """Displays list of domains."""

    template_name = 'os2webscanner/domains.html'
    context_object_name = 'domain_list'

    def get_queryset(self):
        """Get queryset, ordered by url followed by primary key."""
        query_set = super().get_queryset()

        if query_set:
            query_set = query_set.order_by('url', 'pk')

        return query_set


class DomainCreate(RestrictedCreateView):

    """Create a domain view."""

    template_name = 'os2webscanner/domain_form.html'

    def get_form_fields(self):
        """Get the list of form fields.

        The 'validation_status' field will be added to the form if the
        user is a superuser.
        """
        fields = super().get_form_fields()
        if self.request.user.is_superuser:
            fields.append('validation_status')

        self.fields = fields
        return fields

    def get_form(self, form_class=None):

        """Get the form for the view.

        All form widgets will have added the css class 'form-control'.
        """
        if form_class is None:
            form_class = self.get_form_class()

        form = super().get_form(form_class)

        return domain_form_manipulate(form)

    def form_valid(self, form):
        if not self.request.user.is_superuser:
            user_profile = self.request.user.profile
            self.object = form.save(commit=False)
            self.object.organization = user_profile.organization

        """Makes sure authentication info gets stored in db."""
        filedomain = form.save(commit=False)
        authentication = Authentication()
        if 'username' in form.cleaned_data and \
                        form.cleaned_data['username']:
            username = str(form.cleaned_data['username'])
            authentication.username = username
        if 'password' in form.cleaned_data and \
                        form.cleaned_data['password']:
            authentication.set_password(str(form.cleaned_data['password']))
        if 'domain' in form.cleaned_data and \
                        form.cleaned_data['domain']:
            domain = str(form.cleaned_data['domain'])
            authentication.domain = domain
        authentication.save()
        filedomain.authentication = authentication
        filedomain.save()
        return super().form_valid(form)


class DomainUpdate(RestrictedUpdateView):

    """Update a domain view."""
    template_name = 'os2webscanner/domain_form.html'
    old_url = ''

    def get_form_fields(self):
        """Get the list of form fields."""
        fields = super().get_form_fields()

        if self.request.user.is_superuser:
            fields.append('validation_status')

        self.fields = fields
        return fields

    def get_form(self, form_class=None):
        """Get the form for the view.
        """
        if form_class is None:
            form_class = self.get_form_class()

        form = super().get_form(form_class)

        self.old_url = self.get_object().url

        # Adding the form-control class to the elements of the validation form
        # breaks it completely, so we need to do that (by calling
        # domain_form_manipulate) before we create the validation UI
        domain_form_manipulate(form)

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
        if self.old_url != self.object.url:
            self.object.validation_status = Domain.INVALID

        if not self.request.user.is_superuser:
            user_profile = self.request.user.profile
            self.object = form.save(commit=False)
            self.object.organization = user_profile.organization

        domain = form.save(commit=False)
        authentication = domain.authentication
        if 'username' in form.cleaned_data:
            authentication.username = form.cleaned_data['username']
        if 'password' in form.cleaned_data:
            authentication.set_password(str(form.cleaned_data['password']))
        if 'domain' in form.cleaned_data:
            authentication.domain = form.cleaned_data['domain']
        if authentication is not None:
            authentication.save()

        return super().form_valid(form)

