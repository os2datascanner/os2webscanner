from django import forms

from ..validate import validate_domain, get_validation_str

from views import RestrictedListView, RestrictedCreateView, \
    RestrictedUpdateView, RestrictedDetailView, RestrictedDeleteView

from ..models.domain_model import Domain
from ..models.webdomain_model import WebDomain
from ..models.filedomain_model import FileDomain
from ..models.authentication_model import Authentication
from ..aescipher import encrypt, decrypt


class DomainList(RestrictedListView):

    """Displays list of domains."""

    template_name = 'os2webscanner/domains.html'
    context_object_name = 'domain_list'

    def get_queryset(self):
        """Get queryset, ordered by url followed by primary key."""
        query_set = super(DomainList, self).get_queryset()

        if query_set:
            query_set = query_set.order_by('url', 'pk')

        return query_set


class WebDomainList(DomainList):

    """Displays list of domains."""

    model = WebDomain
    type = 'web'


class FileDomainList(DomainList):

    """Displays list of domains."""

    model = FileDomain
    type = 'file'


class DomainCreate(RestrictedCreateView):

    """Create a domain view."""

    template_name = 'os2webscanner/domain_form.html'

    def get_form_fields(self):
        """Get the list of form fields.

        The 'validation_status' field will be added to the form if the
        user is a superuser.
        """
        fields = super(DomainCreate, self).get_form_fields()
        if self.request.user.is_superuser:
            fields.append('validation_status')
        return fields

    def get_form(self, form_class):
        """Get the form for the view.

        All form widgets will have added the css class 'form-control'.
        """
        form = super(DomainCreate, self).get_form(form_class)

        for fname in form.fields:
            f = form.fields[fname]
            f.widget.attrs['class'] = 'form-control'

        return form


class WebDomainCreate(DomainCreate):

    """Web domain create form."""

    model = WebDomain
    fields = ['url', 'exclusion_rules', 'download_sitemap', 'sitemap_url',
              'sitemap']

    def get_success_url(self):
        """The URL to redirect to after successful creation."""
        return '/webdomains/%s/created/' % self.object.pk


class FileDomainCreate(DomainCreate):

    """File domain create form."""

    model = FileDomain
    fields = ['url', 'exclusion_rules']

    def get_form(self, form_class):
        """Adds special field password."""
        form = super(FileDomainCreate, self).get_form(form_class)
        form.fields['username'] = forms.CharField(max_length=1024)
        form.fields['password'] = forms.CharField(max_length=50)
        return form

    def form_valid(self, form):
        """Makes sure password gets encrypted before stored in db."""
        filedomain = form.save(commit=False)
        authentication = Authentication()
        if len(form.cleaned_data['username']) > 0:
            username = str(form.cleaned_data['username'])
            authentication.username = username
        if len(form.cleaned_data['password']) > 0:
            iv, ciphertext = encrypt(str(form.cleaned_data['password']))
            authentication.ciphertext = ciphertext
            authentication.iv = iv
        authentication.save()
        filedomain.authentication = authentication
        filedomain.save()
        return super(FileDomainCreate, self).form_valid(form)

    def get_success_url(self):
        """The URL to redirect to after successful creation."""
        return '/filedomains/%s/created/' % self.object.pk


class DomainUpdate(RestrictedUpdateView):

    """Update a domain view."""
    template_name = 'os2webscanner/domain_form.html'
    old_url = ''

    def get_form_fields(self):
        """Get the list of form fields."""
        fields = super(DomainUpdate, self).get_form_fields()

        if self.request.user.is_superuser:
            fields.append('validation_status')
        elif not self.object.validation_status:
            fields.append('validation_method')

        self.fields = fields
        return fields

    def get_form(self, form_class):
        """Get the form for the view.
        """
        form = super(DomainUpdate, self).get_form(form_class)

        self.old_url = self.get_object().url

        for fname in form.fields:
            f = form.fields[fname]
            f.widget.attrs['class'] = 'form-control'

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

        return super(DomainUpdate, self).form_valid(form)


class WebDomainUpdate(DomainUpdate):
    """Update a web domain view."""

    model = WebDomain
    fields = ['url', 'exclusion_rules', 'download_sitemap',
              'sitemap_url', 'sitemap']

    def get_context_data(self, **kwargs):
        """Get the context used when rendering the template."""
        context = super(WebDomainUpdate, self).get_context_data(**kwargs)
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


class FileDomainUpdate(DomainUpdate):
    """Update a file domain view."""

    model = FileDomain
    fields = ['url', 'exclusion_rules']

    def get_form(self, form_class):
        """Adds special field password and decrypts password."""
        form = super(FileDomainUpdate, self).get_form(form_class)
        filedomain = self.get_object()
        authentication = filedomain.authentication
        form.fields['username'] = forms.CharField(max_length=1024)
        form.fields['password'] = forms.CharField(max_length=50)
        if len(authentication.username) > 0:
            form.fields['username'].initial = authentication.username
        if len(authentication.ciphertext) > 0:
            password = decrypt(str(authentication.iv), str(authentication.ciphertext))
            form.fields['password'].initial = password
        return form

    def form_valid(self, form):
        """Makes sure password gets encrypted before stored in db."""
        filedomain = form.save(commit=False)
        authentication = filedomain.authentication
        authentication.username = str(form.cleaned_data['username'])
        iv, ciphertext = encrypt(str(form.cleaned_data['password']))
        authentication.ciphertext = ciphertext
        authentication.iv = iv
        authentication.save()
        return super(FileDomainUpdate, self).form_valid(form)

    def get_success_url(self):
        """The URL to redirect to after successful updating.

        Will redirect the user to the validate view if the form was submitted
        with the 'save_and_validate' button.
        """
        if 'save_and_validate' in self.request.POST:
            return 'validate/'
        else:
            return '/filedomains/%s/saved/' % self.object.pk


class DomainValidate(RestrictedDetailView):

    """View that handles validation of a domain."""

    model = Domain

    def get_context_data(self, **kwargs):
        """Perform validation and populate the template context."""
        context = super(DomainValidate, self).get_context_data(**kwargs)
        context['validation_status'] = self.object.validation_status
        if not self.object.validation_status:
            result = validate_domain(self.object)

            if result:
                self.object.validation_status = Domain.VALID
                self.object.save()

            context['validation_success'] = result

        return context


class DomainDelete(RestrictedDeleteView):

    """Delete a domain view."""

    model = Domain
    success_url = '/domains/'
