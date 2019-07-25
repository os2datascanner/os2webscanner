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

from django.db import models

from .sensitivity_level import Sensitivity


class Match(models.Model):

    """The data associated with a single match in a single URL."""
    url = models.ForeignKey(
        "Version",
        null=False,
        verbose_name='URL',
        on_delete=models.CASCADE,
        related_name="matches",
    )
    matched_data = models.TextField(verbose_name='Data match')
    matched_rule = models.CharField(max_length=256, verbose_name='Regel match')
    sensitivity = models.IntegerField(choices=Sensitivity.choices,
                                      default=Sensitivity.HIGH,
                                      verbose_name='Følsomhed')
    match_context = models.CharField(max_length=1152, verbose_name='Kontekst')
    page_no = models.IntegerField(null=True, verbose_name='Side')

    @property
    def scan(self):
        return self.url.scan

    def get_matched_rule_display(self):
        """Return a display name for the rule."""
        return Match.get_matched_rule_display_name(self.matched_rule)

    @classmethod
    def get_matched_rule_display_name(cls, rule):
        """Return a display name for the given rule."""
        if rule == 'cpr':
            return "CPR"
        elif rule == 'name':
            return "Navn"
        elif rule == 'address':
            return "Adresse"
        else:
            return rule

    def get_sensitivity_class(self):
        """Return the bootstrap CSS class for the sensitivty."""
        if self.sensitivity == Sensitivity.HIGH:
            return "danger"
        elif self.sensitivity == Sensitivity.LOW:
            return "warning"
        elif self.sensitivity == Sensitivity.OK:
            return "success"

    def __str__(self):
        """Return a string representation of the match."""
        return "Match: %s; [%s] %s <%s>" % (self.get_sensitivity_display(),
                                             self.matched_rule,
                                             self.matched_data, self.url)

    class Meta:
        abstract = False

        verbose_name = 'Match'
        verbose_name_plural = 'Matches'
