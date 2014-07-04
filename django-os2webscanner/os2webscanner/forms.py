"""Contains forms."""

from django.forms import ModelForm
from .models import Scanner


class ScannerForm(ModelForm):

    """A form for creating or updating scanners."""

    class Meta:
        model = Scanner
