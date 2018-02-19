# -*- coding: UTF-8 -*-
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

from subprocess import Popen

from django.db import models
from recurrence.fields import RecurrenceField

from os2webscanner import aescipher
from organization_model import Organization
from group_model import Group
from regexrule_model import RegexRule
from scan_model import Scan
from userprofile_model import UserProfile

base_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


class Scanner(models.Model):

    """A scanner, i.e. a template for actual scanning jobs."""

    CONCRETE_CLASSES = ('WebScanner', 'FileScanner',)

    name = models.CharField(max_length=256, unique=True, null=False,
                            verbose_name='Navn')
    # User login for websites, network drives etc.
    username = models.CharField(max_length=1024, unique=False, blank=True, default='',
                                verbose_name='Bruger navn')
    # One of the two encryption keys for decrypting the password
    iv = models.BinaryField(max_length=32, unique=False, blank=True,
                            verbose_name='InitialiseringsVektor')

    # The encrypted password
    ciphertext = models.BinaryField(max_length=1024, unique=False, blank=True,
                                    verbose_name='Password')

    organization = models.ForeignKey(Organization, null=False,
                                     verbose_name='Organisation')
    group = models.ForeignKey(Group, null=True, blank=True,
                              verbose_name='Gruppe')
    schedule = RecurrenceField(max_length=1024,
                               verbose_name='Planlagt afvikling')
    do_cpr_scan = models.BooleanField(default=True, verbose_name='CPR')
    do_name_scan = models.BooleanField(default=False, verbose_name='Navn')
    do_address_scan = models.BooleanField(default=False,
                                          verbose_name='Adresse')
    do_ocr = models.BooleanField(default=False, verbose_name='Scan billeder')
    do_last_modified_check = models.BooleanField(default=True,
                                                 verbose_name='Tjek sidst ændret dato')
    do_cpr_modulus11 = models.BooleanField(default=True,
                                           verbose_name='Tjek modulus-11')
    do_cpr_ignore_irrelevant = models.BooleanField(
        default=True,
        verbose_name='Ignorer ugyldige fødselsdatoer')
    columns = models.CommaSeparatedIntegerField(max_length=128,
                                                null=True,
                                                blank=True)
    regex_rules = models.ManyToManyField(RegexRule,
                                         blank=True,
                                         verbose_name='Regex regler')
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

    @property
    def set_password(self, password):
        return aescipher.encrypt(password)

    @property
    def get_password(self, iv, cipher):
        return aescipher.decrypt(iv, cipher)



    @property
    def schedule_description(self):
        """A lambda for creating schedule description strings."""
        rules = [r for r in self.schedule.rrules]  # Use r.to_text() to render
        dates = [d for d in self.schedule.rdates]
        if len(rules) > 0 or len(dates) > 0:
            return u"Ja"
        else:
            return u"Nej"

    @property
    def has_active_scans(self):
        """Whether the scanner has active scans."""
        active_scanners = Scan.objects.filter(scanner=self, status__in=(
            Scan.NEW, Scan.STARTED)).count()
        return active_scanners > 0

    @property
    def has_valid_domains(self):
        return len([d for d in self.domains.all() if d.validation_status]) > 0

    # Run error messages
    ALREADY_RUNNING = (
        "Scanneren kunne ikke startes," +
        " fordi der allerede er en scanning i gang for den."
    )
    NO_VALID_DOMAINS = (
        "Scanneren kunne ikke startes," +
        " fordi den ikke har nogen gyldige domæner."
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

    def run(self, test_only=False, blocking=False, user=None):
        """Run a scan with the Scanner.

        Return the Scan object if we started the scanner.
        Return None if there is already a scanner running,
        or if there was a problem running the scanner.
        If test_only is True, only check if we can run a scan, don't actually
        run one.
        """
        if self.has_active_scans:
            return Scanner.ALREADY_RUNNING

        if not self.has_valid_domains:
            return Scanner.NO_VALID_DOMAINS

        # Create a new Scan
        scan = Scan.create(self)
        # Add user as recipient on scan
        if user:
            scan.recipients.add(user.profile)
        # Get path to run script
        SCRAPY_WEBSCANNER_DIR = os.path.join(base_dir, "scrapy-webscanner")

        if test_only:
            return scan

        if not os.path.exists(scan.scan_log_dir):
            os.makedirs(scan.scan_log_dir)
        log_file = open(scan.scan_log_file, "a")

        if not os.path.exists(scan.scan_output_files_dir):
            os.makedirs(scan.scan_output_files_dir)

        try:
            process = Popen([os.path.join(SCRAPY_WEBSCANNER_DIR, "run.sh"),
                             str(scan.pk)], cwd=SCRAPY_WEBSCANNER_DIR,
                            stderr=log_file,
                            stdout=log_file)
            if blocking:
                process.communicate()
        except Exception as e:
            print e
            return None
        return scan

    class Meta:
        abstract = True
        ordering = ['name']
