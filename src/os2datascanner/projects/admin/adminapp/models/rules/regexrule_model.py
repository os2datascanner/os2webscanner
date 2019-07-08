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
from .rule_model import Rule


class RegexRule(Rule):
    """Represents matching rules based on regular expressions."""

    cpr_enabled = models.BooleanField(default=False, verbose_name='Scan CPR')
    do_modulus11 = models.BooleanField(default=False, verbose_name='Tjek modulus-11')
    ignore_irrelevant = models.BooleanField(default=False, verbose_name='Ignorer ugyldige fødselsdatoer')


class RegexPattern(models.Model):
    """
    Represents a regular expression pattern to be added to a RegexRule.
    """

    class Meta:
        verbose_name = 'Pattern'

    regex = models.ForeignKey(RegexRule, null=True, on_delete=models.CASCADE,
                              related_name='patterns', verbose_name='Regex')

    pattern_string = models.CharField(max_length=1024, blank=False,
                                      verbose_name='Udtryk')

    def __str__(self):
        """Return the pattern string."""
        return self.pattern_string
