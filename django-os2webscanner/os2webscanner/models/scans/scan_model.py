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

import datetime
import os
import shutil
from django.conf import settings
from django.core.validators import validate_comma_separated_integer_list
from django.db import models
from django.db.models.aggregates import Count
from django.utils import timezone

from ..domains.domain_model import Domain
from ..regexrule_model import RegexRule
from ..scannerjobs.scanner_model import Scanner
from ..sensitivity_level import Sensitivity
from ..userprofile_model import UserProfile

timezone.activate(timezone.get_default_timezone())


class Scan(models.Model):

    """An actual instance of the scanning process done by a scanner."""

    def __init__(self, *args, **kwargs):
        """Initialize a new scan.
        Stores the old status of the scan for later use.
        """
        super().__init__(*args, **kwargs)
        self._old_status = self.status

    start_time = models.DateTimeField(blank=True, null=True,
                                      verbose_name='Starttidspunkt')
    end_time = models.DateTimeField(blank=True, null=True,
                                    verbose_name='Sluttidspunkt')

    # Begin setup copied from scanner
    scanner = models.ForeignKey(Scanner,
                                null=True, verbose_name='webscanner',
                                related_name='webscans',
                                on_delete=models.SET_NULL)

    domains = models.ManyToManyField(Domain,
                                     verbose_name='Domæner')

    is_visible = models.BooleanField(default=True)

    whitelisted_names = models.TextField(max_length=4096, blank=True,
                                         default="",
                                         verbose_name='Godkendte navne')
    blacklisted_names = models.TextField(max_length=4096, blank=True,
                                         default="",
                                         verbose_name='Sortlistede navne')
    whitelisted_addresses = models.TextField(max_length=4096, blank=True,
                                             default="", verbose_name='Godkendte adresser')
    blacklisted_addresses = models.TextField(
        max_length=4096, blank=True,
        default="",
        verbose_name='Sortlistede adresser'
    )
    whitelisted_cprs = models.TextField(max_length=4096, blank=True,
                                        default="",
                                        verbose_name='Godkendte CPR-numre')
    do_name_scan = models.BooleanField(default=False, verbose_name='Navn')
    do_address_scan = models.BooleanField(default=False,
                                          verbose_name='Adresse')
    do_ocr = models.BooleanField(default=False, verbose_name='Scan billeder')


    do_last_modified_check = models.BooleanField(default=True,
                                                 verbose_name='Tjek sidst ændret dato')

    columns = models.CharField(validators=[validate_comma_separated_integer_list],
                               max_length=128,
                               null=True,
                               blank=True
                               )

    regex_rules = models.ManyToManyField(RegexRule,
                                         blank=True,
                                         verbose_name='Regex-regler',
                                         related_name='scans')
    recipients = models.ManyToManyField(UserProfile, blank=True)

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

    # Scan status
    NEW = "NEW"
    STARTED = "STARTED"
    DONE = "DONE"
    FAILED = "FAILED"

    status_choices = (
        (NEW, "Ny"),
        (STARTED, "I gang"),
        (DONE, "Færdig"),
        (FAILED, "Mislykket"),
    )

    status = models.CharField(max_length=10, choices=status_choices,
                              default=NEW)

    pause_non_ocr_conversions = models.BooleanField(default=False,
                                                    verbose_name='Pause ' +
                                                                 'non-OCR conversions')

    def get_number_of_failed_conversions(self):
        """The number conversions that has failed during this scan."""
        from ..conversionqueueitem_model import ConversionQueueItem
        return ConversionQueueItem.objects.filter(
            url__scan=self,
            status=ConversionQueueItem.FAILED
        ).count()

    @property
    def get_valid_domains(self):
        return self.domains.filter(
            validation_status=Domain.VALID
        )

    @property
    def status_text(self):
        """A display text for the scan's status.

        Relies on the restriction that the status must be one of the allowed
        values.
        """
        text = [t for s, t in Scan.status_choices if self.status == s][0]
        return text

    @property
    def scan_dir(self):
        """The directory associated with this scan."""
        return os.path.join(settings.VAR_DIR, 'scan_%s' % self.pk)

    @property
    def scan_log_dir(self):
        """Return the path to the scan log dir."""
        log_dir = os.path.join(settings.VAR_DIR, 'logs', 'scans')
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        return log_dir

    @property
    def scan_log_file(self):
        """Return the log file path associated with this scan."""
        return os.path.join(self.scan_log_dir, 'scan_%s.log' % self.pk)

    @property
    def scan_output_files_dir(self):
        """Return the path to the scan output files dir."""
        return os.path.join(settings.VAR_DIR, 'output_files')

    @property
    def scan_output_file(self):
        """Return the output file path associated with this scan.

        Note that this currently only supports one output file per scan.
        """
        return os.path.join(self.scan_output_files_dir,
                            'scan_%s.csv' % self.pk)

    # Occurrence log - mainly for the scanner to notify when something FAILS.
    def log_occurrence(self, string):
        with open(self.occurrence_log_file, "a") as f:
            f.write("{0}\n".format(string))

    @property
    def occurrence_log(self):
        try:
            with open(self.occurrence_log_file, "r") as f:
                return f.read()
        except IOError:
            return ""

    @property
    def occurrence_log_file(self):
        """Return the file path to this scan's occurrence log."""
        return os.path.join(self.scan_log_dir, 'occurrence_%s.log' % self.pk)

    # Reason for failure
    reason = models.CharField(max_length=1024, blank=True, default="",
                              verbose_name='Årsag')
    pid = models.IntegerField(null=True, blank=True, verbose_name='Pid')

    @property
    def no_of_matches(self):
        """Return the number of matches for this scan."""
        return self.matches.count()

    @property
    def no_of_critical_matches(self):
        """Return the number of *critical* matches, <= no_of_matches."""
        return self.matches.filter(sensitivity=Sensitivity.HIGH).count()

    def __str__(self):
        """Return the name of the scan's scanner combined with a timestamp."""
        ts = (
            self.start_time
            .astimezone(dateutil.tz.tzlocal())
            .replace(microsecond=0, tzinfo=None)
        )
        return "{} — {}".format(self.scanner, ts)

    def save(self, *args, **kwargs):
        """Save changes to the scan.

        Sets the end_time for the scan, notifies the associated user by email,
        deletes any remaining queue items and deletes the temporary directory
        used by the scan.
        """
        # Pre-save stuff
        if self.status in [Scan.DONE, Scan.FAILED] and \
                (self._old_status != self.status):
            self.end_time = datetime.datetime.now(tz=timezone.utc)

        # Actual save
        super().save(*args, **kwargs)
        # Post-save stuff

        if self.status in [Scan.DONE, Scan.FAILED] and \
                (self._old_status != self.status):
            # Send email
            from os2webscanner.utils import notify_user
            try:
                notify_user(self)
            except IOError:
                self.log_occurrence("Unable to send email notification!")

            self.cleanup_finished_scan()
            self._old_status = self.status

    def cleanup_finished_scan(self, log=False):
        """Delete pending conversion queue items and remove the scan dir."""
        # remove all files associated with the scan
        if self.is_scan_dir_writable():
            self.delete_scan_dir(log)

    @classmethod
    def cleanup_finished_scans(cls, scan_age, log=False):
        """Cleanup convqueue items from finished scans.

        Only Scans that have ended since scan_age ago are considered.
        scan_age should be a timedelta object.
        """
        from django.utils import timezone
        from django.db.models import Q
        oldest_end_time = timezone.localtime(timezone.now()) - scan_age
        inactive_scans = cls.objects.filter(
            Q(status__in=(Scan.DONE, Scan.FAILED)),
            Q(end_time__gt=oldest_end_time) | Q(end_time__isnull=True)
        )

        for scan in inactive_scans:
            scan.delete_all_pending_conversionqueue_items(log)
            scan.cleanup_finished_scan(log=log)

    def delete_all_pending_conversionqueue_items(self, log):
        # Delete all pending conversionqueue items
        from ..conversionqueueitem_model import ConversionQueueItem
        pending_items = ConversionQueueItem.objects.filter(
            url__scan=self,
            status=ConversionQueueItem.NEW
        )
        if log:
            if pending_items.exists():
                print("Deleting %d remaining conversion queue items from "
                      "finished scan %s" % (
                          pending_items.count(), self))
        pending_items.delete()

    def delete_scan_dir(self, log):
        if log:
            print("Deleting scan directory: {}".format(self.scan_dir))
            shutil.rmtree(self.scan_dir, True)
            print('Directory deleted: {}'.format(self.scan_dir))

    @classmethod
    def pause_non_ocr_conversions_on_scans_with_too_many_ocr_items(cls):
        """Pause non-OCR conversions on scans with too many OCR items.

        When the number of OCR items per scan reaches a
        certain threshold (PAUSE_NON_OCR_ITEMS_THRESHOLD), non-OCR conversions
        are paused to allow the number of
        OCR items to fall to a reasonable level. For large scans with OCR
        enabled, this is necessary because so many OCR items are extracted
        from PDFs or Office documents that it exhausts the number of
        available inodes on the filesystem.

        When the number of OCR items falls below the lower threshold
        (RESUME_NON_OCR_ITEMS_THRESHOLD), non-OCR conversions are resumed.
        """
        from ..conversionqueueitem_model import ConversionQueueItem
        ocr_items_by_scan = ConversionQueueItem.objects.filter(
            status=ConversionQueueItem.NEW,
            type="ocr"
        ).values("url__scan").annotate(total=Count("url__scan"))
        for items in ocr_items_by_scan:
            scan = cls.objects.get(pk=items["url__scan"])
            num_ocr_items = items["total"]
            if (not scan.pause_non_ocr_conversions and
                        num_ocr_items > settings.PAUSE_NON_OCR_ITEMS_THRESHOLD):
                print("Pausing non-OCR conversions for scan <%s> (%d) " \
                      "because it has %d OCR items which is over the " \
                      "threshold of %d" % \
                      (scan, scan.pk, num_ocr_items,
                       settings.PAUSE_NON_OCR_ITEMS_THRESHOLD))
                scan.pause_non_ocr_conversions = True
                scan.save()
            elif (scan.pause_non_ocr_conversions and
                          num_ocr_items < settings.RESUME_NON_OCR_ITEMS_THRESHOLD):
                print("Resuming non-OCR conversions for scan <%s> (%d) " \
                      "because it has %d OCR items which is under the " \
                      "threshold of %d" % \
                      (scan, scan.pk, num_ocr_items,
                       settings.RESUME_NON_OCR_ITEMS_THRESHOLD))
                scan.pause_non_ocr_conversions = False
                scan.save()

    def is_scan_dir_writable(self):
        """Return whether the scan's directory exists and is writable."""
        return os.access(self.scan_dir, os.W_OK)

    def get_absolute_url(self):
        """Get the URL for this report - used to format URLs."""
        from django.core.urlresolvers import reverse
        return reverse('report', args=[str(self.id)])

    def set_scan_status_start(self):
        # Update start_time to now and status to STARTED
        self.start_time = datetime.datetime.now(tz=timezone.utc)
        self.status = Scan.STARTED
        self.reason = ""
        pid = os.getpid()
        print('Starting scan job with pid {}'.format(pid))
        self.pid = pid
        self.save()

    def set_scan_status_done(self):
        self.status = Scan.DONE
        self.pid = None
        self.reason = ""
        self.save()

    def set_scan_status_failed(self, reason):
        self.pid = None
        self.status = Scan.FAILED
        if reason is None:
            self.reason = "Killed"
        else:
            self.reason = reason

        self.log_occurrence(
            self.reason
        )
        # TODO: Remove all non-processed conversion queue items.
        self.save()

    # Create method - copies fields from scanner
    def create(self, scanner):
        """ Create and copy fields from scanner. """
        self.is_visible = scanner.is_visible
        self.whitelisted_names = scanner.organization.name_whitelist
        self.blacklisted_names = scanner.organization.name_blacklist
        self.whitelisted_addresses = scanner.organization.address_whitelist
        self.blacklisted_addresses = scanner.organization.address_blacklist
        self.whitelisted_cprs = scanner.organization.cpr_whitelist
        self.do_name_scan = scanner.do_name_scan
        self.do_address_scan = scanner.do_address_scan
        self.do_ocr = scanner.do_ocr
        self.do_last_modified_check = scanner.do_last_modified_check
        self.columns = scanner.columns
        self.output_spreadsheet_file = scanner.output_spreadsheet_file
        self.do_cpr_replace = scanner.do_cpr_replace
        self.cpr_replace_text = scanner.cpr_replace_text
        self.do_name_replace = scanner.do_name_replace
        self.name_replace_text = scanner.name_replace_text
        self.do_address_replace = scanner.do_address_replace
        self.address_replace_text = scanner.address_replace_text
        self.set_status_new(scanner)

        return self

    def set_status_new(self, scanner):
        self.status = Scan.NEW
        self.scanner = scanner
        self.save()
        self.domains.add(*scanner.domains.all())
        self.regex_rules.add(*scanner.regex_rules.all())
        self.recipients.add(*scanner.recipients.all())

    class Meta:
        abstract = False
        db_table = 'os2webscanner_scan'
