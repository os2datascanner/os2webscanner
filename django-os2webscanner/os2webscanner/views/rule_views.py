from .views import RestrictedListView, RestrictedCreateView, \
    RestrictedUpdateView, RestrictedDetailView, RestrictedDeleteView
from ..models.regexrule_model import RegexRule
from ..models.regexpattern_model import RegexPattern

from django import forms
import ipdb


class RuleList(RestrictedListView):
    """Displays list of scanners."""

    model = RegexRule
    template_name = 'os2webscanner/rules.html'


class RuleCreate(RestrictedCreateView):
    """Create a rule view."""

    model = RegexRule
    fields = ['name', 'description', 'sensitivity']

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
        # Then a dynamic form to create multiple pattern fields
        # See - https://www.caktusgroup.com/blog/2018/05/07/creating-dynamic-forms-django/ (Creating a dynamic form)
        patterns = RegexPattern.objects.filter(regex=form.instance)

        for i in range(len(patterns) + 1):
            field_name = 'pattern_%s' % (i,)
            form.fields[field_name] = forms.CharField(required=False)
            # try:
            #     ipdb.set_trace()
            #     self.initial[field_name] = patterns[i].pattern
            # except IndexError:
            #     self.initial[field_name] = ""
            field_name = 'pattern_%s' % (i + 1,)
            form.fields[field_name] = forms.CharField(required=False)
            form.fields[field_name] = ""

            ipdb.set_trace()

        return form

    def form_valid(self, form):
        """
        Interrupting the save method to save the patterns first before saving the RegexRule
        :param form:
        :return:
        """
        RegexRule = form.save(commit=False)
        form_patterns = form.cleaned_data['patterns']
        patterns = set()

        ipdb.set_trace()
        for pattern in form_patterns:
            patterns.add(RegexPattern.objects.create(regex=RegexRule, pattern_string=pattern))

        form.fields['patterns'] = patterns

        return super().form_valid(form)

    def clean(self, form):
        patterns = set()
        i = 0
        field_name = 'pattern_%s' % (i,)
        while form.cleaned_data.get(field_name):
            pattern = form.cleaned_data[field_name]
            if pattern in patterns:
                form.add_error(field_name, 'Duplicate')
            else:
                patterns.add(pattern)
            i += 1
            field_name = 'pattern_%s' % (i,)

        form.cleaned_data['patterns'] = patterns

    def get_success_url(self):
        """The URL to redirect to after successful creation."""
        return '/rules/%s/created/' % self.object.pk


class RuleUpdate(RestrictedUpdateView):
    """Update a rule view."""

    model = RegexRule
    fields = ['name', 'description', 'sensitivity']

    def get_form(self, form_class=None):
        """Get the form for the view.

        All form fields will have the css class 'form-control' added.
        """
        if form_class is None:
            form_class = self.get_form_class()

        form = super().get_form(form_class)
        form.fields['patterns'] = self.object.patterns.all()

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
