# -*- coding: utf-8 -*-
# encoding: utf-8
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

"""Contains Django model for the scanner types."""

import os
import datetime
import json

from django.core.validators import validate_comma_separated_integer_list
from django.db import models

from model_utils.managers import InheritanceManager
from recurrence.fields import RecurrenceField

from ..organization_model import Organization
from ..group_model import Group
from ..regexrule_model import RegexRule
from ..userprofile_model import UserProfile

base_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


class Scanner(models.Model):

    """A scanner, i.e. a template for actual scanning jobs."""
    objects = InheritanceManager()

    name = models.CharField(max_length=256, unique=True, null=False,
                            verbose_name='Navn')

    organization = models.ForeignKey(Organization, null=False,
                                     verbose_name='Organisation')

    group = models.ForeignKey(Group, null=True, blank=True,
                              verbose_name='Gruppe')

    schedule = RecurrenceField(max_length=1024,
                               verbose_name='Planlagt afvikling')

    do_name_scan = models.BooleanField(default=False, verbose_name='Navn')

    do_address_scan = models.BooleanField(default=False,
                                          verbose_name='Adresse')

    do_ocr = models.BooleanField(default=False, verbose_name='Scan billeder')

    do_last_modified_check = models.BooleanField(
        default=True,
        verbose_name='Tjek dato for sidste ændring',
    )

    columns = models.CharField(validators=[validate_comma_separated_integer_list],
                               max_length=128,
                               null=True,
                               blank=True
                               )

    regex_rules = models.ManyToManyField(RegexRule,
                                         blank=True,
                                         verbose_name='Regex-regler')

    recipients = models.ManyToManyField(UserProfile, blank=True,
                                        verbose_name='Modtagere')

    # Spreadsheet annotation and replacement parameters

    # Save a copy of any spreadsheets scanned with annotations
    # in each row where matches were found. If this is enabled and any of
    # the replacement parameters are enabled (e.g. do_cpr_replace), matches
    # will also be replaced with the specified text (e.g. cpr_replace_text).
    output_spreadsheet_file = models.BooleanField(default=False)

    # Replace CPRs?
    do_cpr_replace = models.BooleanField(default=False)

    # Text to replace CPRs with
    cpr_replace_text = models.CharField(max_length=2048, null=True,
                                        blank=True)

    # Replace names?
    do_name_replace = models.BooleanField(default=False)

    # Text to replace names with
    name_replace_text = models.CharField(max_length=2048, null=True,
                                         blank=True)
    # Replace addresses?
    do_address_replace = models.BooleanField(default=False)

    # Text to replace addresses with
    address_replace_text = models.CharField(max_length=2048, null=True,
                                            blank=True)

    is_running = models.BooleanField(default=False)

    @property
    def schedule_description(self):
        """A lambda for creating schedule description strings."""
        rules = [r for r in self.schedule.rrules]  # Use r.to_text() to render
        dates = [d for d in self.schedule.rdates]
        if rules or dates:
            return u"Ja"
        else:
            return u"Nej"

    # Run error messages
    ALREADY_RUNNING = (
        "Scanneren kunne ikke startes," +
        " fordi der allerede er en scanning i gang for den."
    )
    NO_VALID_DOMAINS = (
        "Scanneren kunne ikke startes," +
        " fordi den ikke har nogen gyldige domæner."
    )
    EXCHANGE_EXPORT_IS_RUNNING = (
        "Scanneren kunne ikke startes," +
        " fordi der er en exchange export igang."
    )

    # DON'T USE DIRECTLY !!!
    # Use process_urls property instead.
    encoded_process_urls = models.CharField(
        max_length=262144,
        null=True,
        blank=True
    )
    # Booleans for control of scanners run from web service.
    do_run_synchronously = models.BooleanField(default=False)
    is_visible = models.BooleanField(default=True)

    def _get_process_urls(self):
        s = self.encoded_process_urls
        if s:
            urls = json.loads(s)
        else:
            urls = []
        return urls

    def _set_process_urls(self, urls):
        self.encoded_process_urls = json.dumps(urls)

    process_urls = property(_get_process_urls, _set_process_urls)

    # First possible start time
    FIRST_START_TIME = datetime.time(18, 0)
    # Amount of quarter-hours that can be added to the start time
    STARTTIME_QUARTERS = 6 * 4

    def get_start_time(self):
        """The time of day the Scanner should be automatically started."""
        added_minutes = 15 * (self.pk % Scanner.STARTTIME_QUARTERS)
        added_hours = int(added_minutes / 60)
        added_minutes -= added_hours * 60
        return Scanner.FIRST_START_TIME.replace(
            hour=Scanner.FIRST_START_TIME.hour + added_hours,
            minute=Scanner.FIRST_START_TIME.minute + added_minutes
        )

    @property
    def has_valid_domains(self):
        return self.organization.os2webscanner_domain_organization.filter(validation_status=True).exists()

    @classmethod
    def modulo_for_starttime(cls, time):
        """Convert a datetime.time object to the corresponding modulo value.

        The modulo value can be used to search the database for scanners that
        should be started at the given time by filtering a query with:
            (WebScanner.pk % WebScanner.STARTTIME_QUARTERS) == <modulo_value>
        """
        if(time < cls.FIRST_START_TIME):
            return None
        hours = time.hour - cls.FIRST_START_TIME.hour
        minutes = 60 * hours + time.minute - cls.FIRST_START_TIME.minute
        return int(minutes / 15)

    @property
    def display_name(self):
        """The name used when displaying the scanner on the web page."""
        return "WebScanner '%s'" % self.name

    def __unicode__(self):
        """Return the name of the scanner."""
        return self.name

    def __str__(self):
        """Return the name of the scanner."""
        return self.__unicode__()

    def run(self, type, blocking=False, user=None):
        """Run a scan with the Scanner.

        Return the Scan object if we started the scanner.
        Return None if there is already a scanner running,
        or if there was a problem running the scanner.
        """
        if self.is_running:
            return Scanner.ALREADY_RUNNING

        if not self.has_valid_domains:
            return Scanner.NO_VALID_DOMAINS

        # Create a new Scan
        scan = self.create_scan()
        if isinstance(scan, str):
            return scan
        # Add user as recipient on scan
        if user:
            try:
                profile = user.profile
            except UserProfile.DoesNotExist:
                profile = None

            if profile is not None:
                scan.recipients.add(user.profile)

        import json
        from os2webscanner.amqp_communication import amqp_connection_manager
        queue_name = 'datascanner'
        completed_scans = \
            self.webscans.all().filter(start_time__isnull=False,
                    end_time__isnull=False).order_by('pk')
        last_scan_started_at = \
            completed_scans.last().start_time.isoformat() \
            if completed_scans else None
        message = {
            'type': type,
            'id': scan.pk,
            'logfile': scan.scan_log_file,
            'last_started': last_scan_started_at
        }
        amqp_connection_manager.start_amqp(queue_name)
        amqp_connection_manager.send_message(queue_name, json.dumps(message))
        amqp_connection_manager.close_connection()

        return scan

    def create_scan(self):
        """
        Creates a file scan.
        :return: A file scan object
        """
        from ..scans.scan_model import Scan
        scan = Scan()
        return scan.create(self)

    class Meta:
        abstract = False
        ordering = ['name']
        db_table = 'os2webscanner_scanner'
