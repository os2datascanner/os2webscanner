from .views import RestrictedListView, RestrictedCreateView, \
    RestrictedUpdateView, RestrictedDetailView, RestrictedDeleteView
from ..models.regexrule_model import RegexRule


class RuleList(RestrictedListView):

    """Displays list of scanners."""

    model = RegexRule
    template_name = 'os2webscanner/rules.html'


class RuleCreate(RestrictedCreateView):

    """Create a rule view."""

    model = RegexRule
    fields = ['name', 'match_string', 'description', 'sensitivity']

    def get_form(self, form_class=None):
        """Get the form for the view.

        All form fields will have the css class 'form-control' added.
        """
        if form_class is None:
            form_class = self.get_form_class()

        form = super().get_form(form_class)

        for fname in form.fields:
            f = form.fields[fname]
            f.widget.attrs['class'] = 'form-control'

        return form

    def get_success_url(self):
        """The URL to redirect to after successful creation."""
        return '/rules/%s/created/' % self.object.pk


class RuleUpdate(RestrictedUpdateView):

    """Update a rule view."""

    model = RegexRule
    fields = ['name', 'match_string', 'description', 'sensitivity']

    def get_form(self, form_class=None):
        """Get the form for the view.

        All form fields will have the css class 'form-control' added.
        """
        if form_class is None:
            form_class = self.get_form_class()

        form = super().get_form(form_class)

        for fname in form.fields:
            f = form.fields[fname]
            f.widget.attrs['class'] = 'form-control'

        return form

    def get_success_url(self):
        """The URL to redirect to after successful update."""
        return '/rules/%s/created/' % self.object.pk


class RuleDelete(RestrictedDeleteView):

    """Delete a rule view."""

    model = RegexRule
    fields = ['name', 'match_string', 'description', 'sensitivity']
    success_url = '/rules/'
