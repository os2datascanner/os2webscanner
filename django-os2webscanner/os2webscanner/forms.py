# The contents of this file are subject to the Mozilla Public License
# Version 2.0 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
#    http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# OS2Webscanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (http://www.os2web.dk/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( http://www.os2web.dk/ )
"""Contains forms."""

from django import forms
from django.core.exceptions import ValidationError


class FileUploadForm(forms.Form):
    """This form is for uploading and scanning files - to start with, mainly
    spreadsheets."""

    def validate_filetype(upload_file):
        extension = upload_file.name.split('.')[-1]
        if extension not in ['odp', 'xls', 'xlsx', 'csv', 'pdf']:
            raise ValidationError(
                'Please upload a spreadsheet or a PDF file!'
            )

    scan_file = forms.FileField(label="Fil", validators=[validate_filetype])
    # CPR scan
    do_cpr_scan = forms.BooleanField(label="Scan CPR-numre", initial=True,
                                     required=False)
    do_replace_cpr = forms.BooleanField(label="Erstat CPR-numre",
                                        initial=True, required=False)
    cpr_replacement_text = forms.CharField(label="Erstat match med",
                                           required=False,
                                           initial="xxxxxx-xxxx")
    # Name scan
    do_name_scan = forms.BooleanField(label="Scan navne", initial=True,
                                      required=False)
    do_replace_name = forms.BooleanField(label="Erstat navne",
                                         initial=False, required=False)
    name_replacement_text = forms.CharField(label="Erstat match med",
                                            required=False,
                                            initial="NAVN",
                                            )
    # Address scan
    do_address_scan = forms.BooleanField(label="Scan adresser", initial=True,
                                         required=False)
    do_replace_address = forms.BooleanField(label="Erstat adresser",
                                            initial=False, required=False)
    address_replacement_text = forms.CharField(label="Erstat match med",
                                               required=False,
                                               initial="ADRESSE",
                                               )
    # OCR scan
    do_ocr = forms.BooleanField(label="OCR scan", initial=False,
                                required=False)
    # Column list - ignored if left blank
    column_list = forms.RegexField(
        label="Scan kun kolonner",
        help_text='Angiv kolonner som store bogstaver adskilt med komma',
        regex='^[A-Z,]+$',
        required=False,
        max_length=128
    )
