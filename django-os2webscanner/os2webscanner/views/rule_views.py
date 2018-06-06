from .views import RestrictedListView, RestrictedCreateView, \
    RestrictedUpdateView, RestrictedDetailView, RestrictedDeleteView
from ..models.regexrule_model import RegexRule
from ..models.regexpattern_model import RegexPattern

from django import forms
from django.db import transaction, IntegrityError
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
        # Then a dynamic form to create multiple pattern fields
        # See - https://www.caktusgroup.com/blog/2018/05/07/creating-dynamic-forms-django/ (Creating a dynamic form)
        # ipdb.set_trace()
        patterns = RegexPattern.objects.filter(regex=form.instance)

        for i in range(len(patterns) + 1):
            field_name = 'pattern_%s' % (i,)
            form.fields[field_name] = forms.CharField(required=False)

        field_name = 'pattern_%s' % (i + 1,)
        form.fields[field_name] = forms.CharField(required=False)
        # form.fields[field_name] = ""

        return form

    def form_valid(self, form):
        """
        validate all the form first
        :param form:
        :return:
        """

        # self.clean(form)
        form_cleaned_data = form.cleaned_data
        form.cleaned_data['patterns'] = self._get_patterns_from(form)
        form_patterns = form.cleaned_data['patterns']
        ipdb.set_trace()

        try:
            with transaction.atomic():
                regexrule = form.save(commit=False)
                regexrule.name = form_cleaned_data['name']
                regexrule.sensitivity = form_cleaned_data['sensitivity']
                regexrule.description = form_cleaned_data['description']
                regexrule.organization = form_cleaned_data['organization']
                # regexrule.patterns_set.all().delete()
                regexrule.save()
                ipdb.set_trace()
                for pattern in form_patterns:
                    r_ = RegexPattern.objects.create(regex=regexrule, pattern_string=pattern)
                    ret = r_.save()
                    ipdb.set_trace()
                    # regexrule.patterns_set.add(r_)
                return super().form_valid(form)
        except:
            return super().form_invalid(form)

    def _get_patterns_from(self, form):
        """
        scrape the patterns from the form
        :param form:
        :return:
        """
        patterns = set()
        i = 0
        field_name = 'pattern_%s' % (i,)
        ipdb.set_trace()
        while form.cleaned_data.get(field_name):
            pattern = form.cleaned_data[field_name]
            if pattern in patterns:
                form.add_error(field_name, 'Duplicate')
            else:
                patterns.add(pattern)
            i += 1
            # remove the pattern_[x] field
            form.cleaned_data.pop(field_name)
            field_name = 'pattern_%s' % (i,)

        ipdb.set_trace()
        return patterns

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
