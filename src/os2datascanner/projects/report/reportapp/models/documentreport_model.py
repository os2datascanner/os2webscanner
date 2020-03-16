from typing import NamedTuple

from django.db import models
from django.contrib.postgres.fields import JSONField

from os2datascanner.engine2.model.core import Handle
from os2datascanner.engine2.rules.rule import Sensitivity


class MatchesMessage(NamedTuple):
    scan_spec: dict
    handle: Handle
    matched: bool
    matches: list

    @property
    def sensitivity(self):
        """Computes the overall sensitivity of the matches contained in this
        message (i.e., the highest sensitivity of any submatch), or None if
        there are no matches."""
        if not self.matches:
            return None
        else:

            def _cms(match):
                if "sensitivity" in match["rule"]:
                    return match["rule"]["sensitivity"] or 0
                else:
                    return 0
            return Sensitivity(max([_cms(match) for match in self.matches]))


class DocumentReport(models.Model):
    path = models.CharField(max_length=2000, verbose_name="Path")
    # It could be that the meta data should not be part of the jsonfield...
    data = JSONField(null=True)

    def _str_(self):
        return self.path

    @property
    def matches(self):
        matches = self.data.get("matches")
        return MatchesMessage(
                scan_spec=matches["scan_spec"],
                handle=Handle.from_json_object(matches["handle"]),
                matched=matches["matched"],
                matches=matches["matches"]) if matches else None

    class Meta:
        verbose_name_plural = "Document reports"
