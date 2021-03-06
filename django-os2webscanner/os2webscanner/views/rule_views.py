from .views import RestrictedListView, RestrictedCreateView, \
    RestrictedUpdateView, RestrictedDeleteView
from ..models.regexrule_model import RegexRule
from ..models.regexpattern_model import RegexPattern

from django import forms
from django.db import transaction

class RuleList(RestrictedListView):
    """Displays list of scanners."""

    model = RegexRule
    template_name = 'os2webscanner/rules.html'


class RuleCreate(RestrictedCreateView):
    """Create a rule view."""

    model = RegexRule
    fields = ['name', 'description', 'sensitivity', 'cpr_enabled', 'do_modulus11', 'ignore_irrelevant']

    def get_form(self, form_class=None):
        """Get the form for the view.
        All form fields will have the css class 'form-control' added.
        """
        if form_class is None:
            form_class = self.get_form_class()

        form = super().get_form(form_class)
        # Then a dynamic form to create multiple pattern fields
        # See - https://www.caktusgroup.com/blog/2018/05/07/creating-dynamic-forms-django/ (Creating a dynamic form)
        self.patterns = extract_pattern_fields(form.data)

        idx = 0
        if 'cpr_enabled' in form.data:
            is_cpr_enabled = True
        else:
            is_cpr_enabled = False

        for field_name, value in self.patterns:
            form.fields[field_name] = forms.CharField(required=False if idx > 0 or is_cpr_enabled else True, initial=value,
                                                      label='Udtryk')
            idx += 1

        return form

    def form_valid(self, form):
        """
        validate all the form first
        :param form:
        :return:
        """
        form_cleaned_data = form.cleaned_data
        form_patterns = [form.cleaned_data[field_name] for field_name in form.cleaned_data if
                         field_name.startswith('pattern_') and form.cleaned_data[field_name] != '']

        try:
            with transaction.atomic():
                regexrule = form.save(commit=False)
                regexrule.name = form_cleaned_data['name']
                regexrule.sensitivity = form_cleaned_data['sensitivity']
                regexrule.description = form_cleaned_data['description']
                regexrule.organization = form_cleaned_data['organization']
                regexrule.save()

                for pattern in form_patterns:
                    r_ = RegexPattern.objects.create(regex=regexrule, pattern_string=pattern)
                    r_.save()

                return super().form_valid(form)
        except:
            return super().form_invalid(form)

    def get_pattern_fields(self):
        """
        Used in the template to get the field names and their values
        :return:
        """

        form_fields = self.get_form().fields
        for field_name in form_fields:
            if field_name.startswith('pattern_'):
                yield (field_name, form_fields.get(field_name).initial)

    def get_success_url(self):
        """The URL to redirect to after successful creation."""
        return '/rules/%s/created/' % self.object.pk


class RuleUpdate(RestrictedUpdateView):
    """Update a rule view."""

    model = RegexRule
    fields = ['name', 'description', 'sensitivity', 'cpr_enabled', 'do_modulus11', 'ignore_irrelevant']

    def get_form(self, form_class=None):
        """Get the form for the view.

        All form fields will have the css class 'form-control' added.
        """
        if form_class is None:
            form_class = self.get_form_class()

        form = super().get_form(form_class)
        regex_patterns = self.object.patterns.all().order_by('-id')

        if not form.data:
            # create extra fields to hold the pattern strings

            if 'cpr_enabled' in form.changed_data: # we can't use form.data when first rendering the edit form; instead, we need to look at which data was changed compared to initial values
                is_cpr_enabled = True
            else:
                is_cpr_enabled = False

            if len(regex_patterns) == 0: # if we have no patterns already, we should at least render one field
                form.fields['pattern_0'] = forms.CharField(required=False if is_cpr_enabled else True, initial='', label='Udtryk')
            else: # otherwise, render the appropriate number of fields
                for i in range(len(regex_patterns)):
                    field_name = 'pattern_%s' % (i,)
                    form.fields[field_name] = forms.CharField(required=False if i > 0 or is_cpr_enabled else True,
                                                              initial=regex_patterns[i].pattern_string, label='Udtryk')
        else:
            self.patterns = extract_pattern_fields(form.data)

            if 'cpr_enabled' in form.data:
                is_cpr_enabled = True
            else:
                is_cpr_enabled = False

            idx = 0
            for field_name, value in self.patterns:
                form.fields[field_name] = forms.CharField(required=False if idx > 0 or is_cpr_enabled else True, initial=value,
                                                          label='Udtryk')
                idx += 1

        # assign class attribute to all fields
        for fname in form.fields:
            f = form.fields[fname]
            f.widget.attrs['class'] = 'form-control'

        return form

    def form_valid(self, form):
        """
        validate all the form first
        :param form:
        :return:
        """
        form_cleaned_data = form.cleaned_data
        form_patterns = [form.cleaned_data[field_name] for field_name in form.cleaned_data if
                         field_name.startswith('pattern_') and form.cleaned_data[field_name] != '']

        try:
            with transaction.atomic():
                self.object.patterns.all().delete()
                regexrule = form.save(commit=False)
                regexrule.name = form_cleaned_data['name']
                regexrule.sensitivity = form_cleaned_data['sensitivity']
                regexrule.description = form_cleaned_data['description']
                regexrule.organization = form_cleaned_data['organization']
                regexrule.save()

                for pattern in form_patterns:
                    r_ = RegexPattern.objects.create(regex=regexrule, pattern_string=pattern)
                    r_.save()

                return super().form_valid(form)
        except:
            return super().form_invalid(form)

    def get_pattern_fields(self):
        """
        Used in the template to get the field names and their values
        :return:
        """

        form_fields = self.get_form().fields

        for field_name in form_fields:
            if field_name.startswith('pattern_'):
                yield (field_name, form_fields.get(field_name).initial)

    def get_success_url(self):
        """The URL to redirect to after successful update."""
        return '/rules/%s/created/' % self.object.pk


class RuleDelete(RestrictedDeleteView):
    """Delete a rule view."""

    model = RegexRule
    success_url = '/rules/'


'''============ Methods required by multiple views ============'''


def extract_pattern_fields(form_fields):
    if not form_fields:
        return [('pattern_0', '')]

    return [(field_name, form_fields[field_name]) for field_name in form_fields if
            field_name.startswith('pattern_')]
