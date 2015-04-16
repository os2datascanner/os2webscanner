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

"""Contains Django models for the Webscanner."""
from django.db.models.aggregates import Count
from urlparse import urljoin

import os
import shutil
from subprocess import Popen
import re
import datetime
import json

from django.db import models
from django.contrib.auth.models import User
from recurrence.fields import RecurrenceField

from django.conf import settings


base_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


# Sensitivity values
class Sensitivity:

    """Name space for sensitivity values."""

    HIGH = 2
    LOW = 1
    OK = 0

    choices = (
        (OK, u'Grøn'),
        (LOW, u'Gul'),
        (HIGH, u'Rød'),
    )


class Organization(models.Model):

    """Represents the organization for each user and scanner, etc.

    Users can only see material related to their own organization.
    """

    name = models.CharField(max_length=256, unique=True, verbose_name='Navn')
    contact_email = models.CharField(max_length=256, verbose_name='Email')
    contact_phone = models.CharField(max_length=256, verbose_name='Telefon')
    do_use_groups = models.BooleanField(default=False,
                                        editable=settings.DO_USE_GROUPS)

    name_whitelist = models.TextField(blank=True,
                                       default="",
                                       verbose_name='Godkendte navne')
    name_blacklist = models.TextField(blank=True,
                                       default="",
                                       verbose_name='Sortlistede navne')
    address_whitelist = models.TextField(blank=True,
                                       default="",
                                       verbose_name='Godkendte adresser')
    address_blacklist = models.TextField(blank=True,
                                       default="",
                                       verbose_name='Sortlistede adresser')

    def __unicode__(self):
        """Return the name of the organization."""
        return self.name


class UserProfile(models.Model):

    """OS2Webscanner specific user profile.

    Each user MUST be associated with an organization.
    """

    organization = models.ForeignKey(Organization,
                                     null=False,
                                     verbose_name='Organisation')
    user = models.ForeignKey(User,
                             unique=True,
                             related_name='profile',
                             verbose_name='Bruger')
    is_group_admin = models.BooleanField(default=False)
    is_upload_only = models.BooleanField(default=False)

    @property
    def is_groups_enabled(self):
        """Whether to activate groups in GUI."""
        return settings.DO_USE_GROUPS

    def __unicode__(self):
        """Return the user's username."""
        return self.user.username


class Group(models.Model):
    """Represents the group or sub-organisation."""
    name = models.CharField(max_length=256, unique=True, verbose_name='Navn')
    contact_email = models.CharField(max_length=256, verbose_name='Email')
    contact_phone = models.CharField(max_length=256, verbose_name='Telefon')
    user_profiles = models.ManyToManyField(UserProfile, null=True, blank=True,
                                           verbose_name='Brugere',
                                           related_name='groups')
    organization = models.ForeignKey(Organization,
                                     null=False,
                                     related_name='groups',
                                     verbose_name='Organisation')

    def __unicode__(self):
        """Return the name of the group."""
        return self.name

    class Meta:
        """Ordering and other options."""
        ordering = ['name']

    @property
    def display_name(self):
        """The name used when displaying the domain on the web page."""
        return "Group '%s'" % self.__unicode__()


class Domain(models.Model):

    """Represents a domain to be scanned."""

    # Validation status

    VALID = 1
    INVALID = 0

    validation_choices = (
        (INVALID, "Ugyldig"),
        (VALID, "Gyldig"),
    )

    # Validation methods

    ROBOTSTXT = 0
    WEBSCANFILE = 1
    METAFIELD = 2

    validation_method_choices = (
        (ROBOTSTXT, 'robots.txt'),
        (WEBSCANFILE, 'webscan.html'),
        (METAFIELD, 'Meta-felt'),
    )

    url = models.CharField(max_length=2048, verbose_name='Url')
    organization = models.ForeignKey(Organization,
                                     null=False,
                                     related_name='domains',
                                     verbose_name='Organisation')
    group = models.ForeignKey(Group,
                              null=True,
                              blank=True,
                              related_name='domains',
                              verbose_name='Gruppe')
    validation_status = models.IntegerField(choices=validation_choices,
                                            default=INVALID,
                                            verbose_name='Valideringsstatus')
    validation_method = models.IntegerField(choices=validation_method_choices,
                                            default=ROBOTSTXT,
                                            verbose_name='Valideringsmetode')
    exclusion_rules = models.TextField(blank=True,
                                       default="",
                                       verbose_name='Ekskluderingsregler')
    sitemap = models.FileField(upload_to='sitemaps',
                               blank=True,
                               verbose_name='Sitemap Fil')

    sitemap_url = models.CharField(max_length=2048,
                                   blank=True,
                                   default="",
                                   verbose_name='Sitemap Url')

    download_sitemap = models.BooleanField(default=True,
                                           verbose_name='Hent Sitemap fra '
                                                        'serveren')

    @property
    def display_name(self):
        """The name used when displaying the domain on the web page."""
        return "Domain '%s'" % self.root_url

    def exclusion_rule_list(self):
        """Return the exclusion rules as a list of strings or regexes."""
        REGEX_PREFIX = "regex:"
        rules = []
        for line in self.exclusion_rules.splitlines():
            line = line.strip()
            if line.startswith(REGEX_PREFIX):
                rules.append(re.compile(line[len(REGEX_PREFIX):],
                                        re.IGNORECASE))
            else:
                rules.append(line)
        return rules

    @property
    def root_url(self):
        """Return the root url of the domain."""
        url = self.url.replace('*.', '')
        if (not self.url.startswith('http://') and not
            self.url.startswith('https://')):
            return 'http://%s/' % url
        else:
            return url

    @property
    def sitemap_full_path(self):
        """Get the absolute path to the uploaded sitemap.xml file."""
        return "%s/%s" % (settings.MEDIA_ROOT, self.sitemap.url)

    @property
    def default_sitemap_path(self):
        return "/sitemap.xml"

    def get_sitemap_url(self):
        """Get the URL of the sitemap.xml file.

        This will be the URL specified by the user, or if not present, the
        URL of the default sitemap.xml file.
        If downloading of the sitemap.xml file is disabled, this will return
        None.
        """
        if not self.download_sitemap:
            return None
        else:
            sitemap_url = self.sitemap_url or self.default_sitemap_path
            return urljoin(self.root_url, sitemap_url)

    def get_absolute_url(self):
        """Get the absolute URL for domains."""
        return '/domains/'

    def __unicode__(self):
        """Return the URL for the domain."""
        return self.url


class RegexRule(models.Model):

    """Represents matching rules based on regular expressions."""

    name = models.CharField(max_length=256, unique=True, null=False,
                            verbose_name='Navn')
    organization = models.ForeignKey(Organization, null=False,
                                     verbose_name='Organisation')
    group = models.ForeignKey(Group, null=True, blank=True,
                              verbose_name='Gruppe')
    match_string = models.CharField(max_length=1024, blank=False,
                                    verbose_name='Udtryk')

    description = models.TextField(verbose_name='Beskrivelse')
    sensitivity = models.IntegerField(choices=Sensitivity.choices,
                                      default=Sensitivity.HIGH,
                                      verbose_name='Følsomhed')

    @property
    def display_name(self):
        """The name used when displaying the regexrule on the web page."""
        return "Regel '%s'" % self.name

    def get_absolute_url(self):
        """Get the absolute URL for rules."""
        return '/rules/'

    def __unicode__(self):
        """Return the name of the rule."""
        return self.name


class Scanner(models.Model):

    """A scanner, i.e. a template for actual scanning jobs."""

    name = models.CharField(max_length=256, unique=True, null=False,
                            verbose_name='Navn')
    organization = models.ForeignKey(Organization, null=False,
                                     verbose_name='Organisation')
    group = models.ForeignKey(Group, null=True, blank=True,
                                     verbose_name='Gruppe')
    schedule = RecurrenceField(max_length=1024,
                               verbose_name='Planlagt afvikling')
    domains = models.ManyToManyField(Domain, related_name='scanners',
                                     null=False, verbose_name='Domæner')
    do_cpr_scan = models.BooleanField(default=True, verbose_name='CPR')
    do_name_scan = models.BooleanField(default=False, verbose_name='Navn')
    do_address_scan = models.BooleanField(default=False,
                                          verbose_name='Adresse')
    do_ocr = models.BooleanField(default=False, verbose_name='Scan billeder?')
    do_cpr_modulus11 = models.BooleanField(default=True,
                                           verbose_name='Check modulus-11')
    do_cpr_ignore_irrelevant = models.BooleanField(
        default=True,
        verbose_name='Ignorer irrelevante fødselsdatoer')
    do_link_check = models.BooleanField(default=False,
                                        verbose_name='Linkcheck')
    do_external_link_check = models.BooleanField(default=False,
                                                 verbose_name='Check ' +
                                                              'eksterne links')
    do_last_modified_check = models.BooleanField(default=True,
                                                 verbose_name='Check ' +
                                                              'Last-Modified')
    do_last_modified_check_head_request = models.BooleanField(
        default=True,
        verbose_name='Brug HEAD request'
    )
    columns = models.CommaSeparatedIntegerField(max_length=128,
                                                null=True,
                                                blank=True)
    regex_rules = models.ManyToManyField(RegexRule,
                                         blank=True,
                                         null=True,
                                         verbose_name='Regex regler')
    recipients = models.ManyToManyField(UserProfile, null=True, blank=True,
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
            (Scanner.pk % Scanner.STARTTIME_QUARTERS) == <modulo_value>
        """
        if(time < cls.FIRST_START_TIME):
            return None
        hours = time.hour - cls.FIRST_START_TIME.hour
        minutes = 60 * hours + time.minute - cls.FIRST_START_TIME.minute
        return int(minutes / 15)

    @property
    def display_name(self):
        """The name used when displaying the scanner on the web page."""
        return "Scanner '%s'" % self.name

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
    ALREADY_RUNNING = ("Scanneren kunne ikke startes," +
                        " fordi der allerede er en scanning i gang for den.")
    NO_VALID_DOMAINS = ("Scanneren kunne ikke startes," +
                         " fordi den ikke har nogen gyldige domæner.")

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
            scan.recipients.add(user.get_profile())
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

    def get_absolute_url(self):
        """Get the absolute URL for scanners."""
        return '/scanners/'

    def __unicode__(self):
        """Return the name of the scanner."""
        return self.name

    class Meta:
        ordering = ['name']


class Scan(models.Model):

    """An actual instance of the scanning process done by a scanner."""

    scanner = models.ForeignKey(Scanner, null=False, verbose_name='Scanner',
                                related_name='scans')
    start_time = models.DateTimeField(blank=True, null=True,
                                      verbose_name='Starttidspunkt')
    end_time = models.DateTimeField(blank=True, null=True,
                                    verbose_name='Sluttidspunkt')

    # Begin setup copied from scanner

    is_visible = models.BooleanField(default=True)

    whitelisted_names = models.TextField(max_length=4096, blank=True,
                                         default="",
                                         verbose_name='Godkendte navne')
    blacklisted_names = models.TextField(max_length=4096, blank=True,
                                         default="",
                                         verbose_name='Sortlistede navne')
    whitelisted_addresses = models.TextField(max_length=4096, blank=True,
                                         default="",
                                         verbose_name='Godkendte adresser')
    blacklisted_addresses = models.TextField(max_length=4096, blank=True,
                                         default="",
                                         verbose_name='Sortlistede adresser')
    domains = models.ManyToManyField(Domain,
                                     null=True,
                                     verbose_name='Domæner')
    do_cpr_scan = models.BooleanField(default=True, verbose_name='CPR')
    do_name_scan = models.BooleanField(default=False, verbose_name='Navn')
    do_address_scan = models.BooleanField(default=False,
                                          verbose_name='Adresse')
    do_ocr = models.BooleanField(default=False, verbose_name='Scan billeder?')
    do_cpr_modulus11 = models.BooleanField(default=True,
                                           verbose_name='Check modulus-11')
    do_cpr_ignore_irrelevant = models.BooleanField(
        default=True,
        verbose_name='Ignorer irrelevante fødselsdatoer')
    do_link_check = models.BooleanField(default=False,
                                        verbose_name='Linkcheck')
    do_external_link_check = models.BooleanField(default=False,
                                                 verbose_name='Check ' +
                                                              'externe links')
    do_last_modified_check = models.BooleanField(default=True,
                                                 verbose_name='Check ' +
                                                              'Last-Modified')
    do_last_modified_check_head_request = models.BooleanField(
        default=True,
        verbose_name='Brug HEAD request'
    )
    columns = models.CommaSeparatedIntegerField(max_length=128,
                                                null=True,
                                                blank=True)
    regex_rules = models.ManyToManyField(RegexRule,
                                         blank=True,
                                         null=True,
                                         verbose_name='Regex regler')
    recipients = models.ManyToManyField(UserProfile, null=True, blank=True)

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

    # END setup copied from scanner

    # Create method - copies fields from scanner
    @classmethod
    def create(scan_cls, scanner):
        """ Create and copy fields from scanner. """
        scan = scan_cls(
            is_visible=scanner.is_visible,
            whitelisted_names=scanner.organization.name_whitelist,
            blacklisted_names=scanner.organization.name_blacklist,
            whitelisted_addresses=scanner.organization.address_whitelist,
            blacklisted_addresses=scanner.organization.address_blacklist,
            do_cpr_scan=scanner.do_cpr_scan,
            do_name_scan=scanner.do_name_scan,
            do_address_scan=scanner.do_address_scan,
            do_ocr=scanner.do_ocr,
            do_cpr_modulus11=scanner.do_cpr_modulus11,
            do_cpr_ignore_irrelevant=scanner.do_cpr_ignore_irrelevant,
            do_link_check=scanner.do_link_check,
            do_external_link_check=scanner.do_external_link_check,
            do_last_modified_check=scanner.do_last_modified_check,
            do_last_modified_check_head_request=scanner.
            do_last_modified_check_head_request,
            columns=scanner.columns,
            output_spreadsheet_file=scanner.output_spreadsheet_file,
            do_cpr_replace=scanner.do_cpr_replace,
            cpr_replace_text=scanner.cpr_replace_text,
            do_name_replace=scanner.do_name_replace,
            name_replace_text=scanner.name_replace_text,
            do_address_replace=scanner.do_address_replace,
            address_replace_text=scanner.address_replace_text
        )
        #
        scan.status = Scan.NEW
        scan.scanner = scanner
        scan.save()
        scan.domains.add(*scanner.domains.all())
        scan.regex_rules.add(*scanner.regex_rules.all())
        scan.recipients.add(*scanner.recipients.all())

        return scan

    # Scan status
    NEW = "NEW"
    STARTED = "STARTED"
    DONE = "DONE"
    FAILED = "FAILED"

    status_choices = (
        (NEW, "Ny"),
        (STARTED, "I gang"),
        (DONE, "OK"),
        (FAILED, "Fejlet"),
    )

    status = models.CharField(max_length=10, choices=status_choices,
                              default=NEW)

    pause_non_ocr_conversions = models.BooleanField(default=False,
                                                    verbose_name='Pause ' +
                                                    'non-OCR conversions')

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
        return os.path.join(settings.VAR_DIR, 'logs', 'scans')

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

    def get_number_of_failed_conversions(self):
        """The number conversions that has failed during this scan."""
        return ConversionQueueItem.objects.filter(
            url__scan=self,
            status=ConversionQueueItem.FAILED
        ).count()

    @property
    def no_of_matches(self):
        """Return the number of matches for this scan."""
        return self.matches.count()

    @property
    def no_of_critical_matches(self):
        """Return the number of *critical* matches, <= no_of_matches."""
        return self.matches.filter(sensitivity=Sensitivity.HIGH).count()

    @property
    def no_of_broken_links(self):
        """Return the number of broken links for this scan."""
        return self.urls.exclude(status_code__isnull=True).count()

    def __unicode__(self):
        """Return the name of the scan's scanner."""
        try:
            return "SCAN: " + self.scanner.name
        except:
            return "ORPHANED SCAN: " + str(self.id)

    def save(self, *args, **kwargs):
        """Save changes to the scan.

        Sets the end_time for the scan, notifies the associated user by email,
        deletes any remaining queue items and deletes the temporary directory
        used by the scan.
        """
        # Pre-save stuff
        if (self.status in [Scan.DONE, Scan.FAILED] and
            (self._old_status != self.status)):
            self.end_time = datetime.datetime.now()
        # Actual save
        super(Scan, self).save(*args, **kwargs)
        # Post-save stuff

        if (self.status in [Scan.DONE, Scan.FAILED] and
            (self._old_status != self.status)):
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
        # Delete all pending conversionqueue items
        pending_items = ConversionQueueItem.objects.filter(
            url__scan=self,
            status=ConversionQueueItem.NEW
        )
        if log:
            if pending_items.exists():
                print "Deleting %d remaining conversion queue items from " \
                      "finished scan %s" % (
                    pending_items.count(), self)

        pending_items.delete()

        # remove all files associated with the scan
        if self.is_scan_dir_writable():
            if log:
                print "Deleting scan directory: %s" % self.scan_dir
            shutil.rmtree(self.scan_dir, True)

    @classmethod
    def cleanup_finished_scans(cls, scan_age, log=False):
        """Cleanup convqueue items from finished scans.

        Only Scans that have ended since scan_age ago are considered.
        scan_age should be a timedelta object.
        """
        from django.utils import timezone
        from django.db.models import Q
        oldest_end_time = timezone.localtime(timezone.now()) - scan_age
        inactive_scans = Scan.objects.filter(
            Q(status__in=(Scan.DONE, Scan.FAILED)),
            Q(end_time__gt=oldest_end_time) | Q(end_time__isnull=True)
        )
        for scan in inactive_scans:
            scan.cleanup_finished_scan(log=log)

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
        ocr_items_by_scan = ConversionQueueItem.objects.filter(
            status=ConversionQueueItem.NEW,
            type="ocr"
        ).values("url__scan").annotate(total=Count("url__scan"))
        for items in ocr_items_by_scan:
            scan = Scan.objects.get(pk=items["url__scan"])
            num_ocr_items = items["total"]
            if (not scan.pause_non_ocr_conversions and
                    num_ocr_items > settings.PAUSE_NON_OCR_ITEMS_THRESHOLD):
                print "Pausing non-OCR conversions for scan <%s> (%d) " \
                      "because it has %d OCR items which is over the " \
                      "threshold of %d" % \
                      (scan, scan.pk, num_ocr_items,
                       settings.PAUSE_NON_OCR_ITEMS_THRESHOLD)
                scan.pause_non_ocr_conversions = True
                scan.save()
            elif (scan.pause_non_ocr_conversions and
                  num_ocr_items < settings.RESUME_NON_OCR_ITEMS_THRESHOLD):
                print "Resuming non-OCR conversions for scan <%s> (%d) " \
                      "because it has %d OCR items which is under the " \
                      "threshold of %d" % \
                      (scan, scan.pk, num_ocr_items,
                       settings.RESUME_NON_OCR_ITEMS_THRESHOLD)
                scan.pause_non_ocr_conversions = False
                scan.save()

    def is_scan_dir_writable(self):
        """Return whether the scan's directory exists and is writable."""
        return os.access(self.scan_dir, os.W_OK)

    def __init__(self, *args, **kwargs):
        """Initialize a new scan.

        Stores the old status of the scan for later use.
        """
        super(Scan, self).__init__(*args, **kwargs)
        self._old_status = self.status

    def get_absolute_url(self):
        """Get the URL for this report - used to format URLs."""
        from django.core.urlresolvers import reverse
        return reverse('report', args=[str(self.id)])


class Url(models.Model):

    """A representation of an actual URL on a domain with its MIME type."""

    url = models.CharField(max_length=2048, verbose_name='Url')
    mime_type = models.CharField(max_length=256, verbose_name='Mime-type')
    scan = models.ForeignKey(Scan, null=False, verbose_name='Scan',
                             related_name='urls')
    status_code = models.IntegerField(blank=True, null=True,
                                      verbose_name='Status code')
    status_message = models.CharField(blank=True, null=True, max_length=256,
                                      verbose_name='Status ' + 'Message')
    referrers = models.ManyToManyField("ReferrerUrl",
                                       related_name='linked_urls',
                                       null=True, verbose_name='Referrers')

    def __unicode__(self):
        """Return the URL."""
        return self.url

    @property
    def tmp_dir(self):
        """The path to the temporary directory associated with this url."""
        return os.path.join(self.scan.scan_dir, 'url_item_%d' % (self.pk))


class Match(models.Model):

    """The data associated with a single match in a single URL."""

    url = models.ForeignKey(Url, null=False, verbose_name='Url')
    scan = models.ForeignKey(Scan, null=False, verbose_name='Scan',
                             related_name='matches')
    matched_data = models.CharField(max_length=1024, verbose_name='Data match')
    matched_rule = models.CharField(max_length=256, verbose_name='Regel match')
    sensitivity = models.IntegerField(choices=Sensitivity.choices,
                                      default=Sensitivity.HIGH,
                                      verbose_name='Følsomhed')

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

    def __unicode__(self):
        """Return a string representation of the match."""
        return u"Match: %s; [%s] %s <%s>" % (self.get_sensitivity_display(),
                                             self.matched_rule,
                                             self.matched_data, self.url)


class ConversionQueueItem(models.Model):

    """Represents an item in the conversion queue."""

    file = models.CharField(max_length=4096, verbose_name='Fil')
    type = models.CharField(max_length=256, verbose_name='Type')
    url = models.ForeignKey(Url, null=False, verbose_name='Url')

    # Note that SUCCESS is indicated by just deleting the record
    NEW = "NEW"
    PROCESSING = "PROCESSING"
    FAILED = "FAILED"

    status_choices = (
        (NEW, "Ny"),
        (PROCESSING, "I gang"),
        (FAILED, "Fejlet"),
    )
    status = models.CharField(max_length=10, choices=status_choices,
                              default=NEW, verbose_name='Status')

    process_id = models.IntegerField(blank=True, null=True,
                                     verbose_name='Proces id')
    process_start_time = models.DateTimeField(
        blank=True, null=True, verbose_name='Proces starttidspunkt'
    )

    @property
    def file_path(self):
        """Return the full path to the conversion queue item's file."""
        return self.file

    @property
    def tmp_dir(self):
        """The path to the temporary dir associated with this queue item."""
        return os.path.join(
            self.url.scan.scan_dir,
            'queue_item_%d' % (self.pk)
        )

    def delete_tmp_dir(self):
        """Delete the item's temp dir if it is writable."""
        if os.access(self.tmp_dir, os.W_OK):
            shutil.rmtree(self.tmp_dir, True)


class ReferrerUrl(models.Model):

    """A representation of a referrer URL."""

    url = models.CharField(max_length=2048, verbose_name='Url')
    scan = models.ForeignKey(Scan, null=False, verbose_name='Scan')

    def __unicode__(self):
        """Return the URL."""
        return self.url


class UrlLastModified(models.Model):

    """A representation of a URL, its last-modifed date, and its links."""

    url = models.CharField(max_length=2048, verbose_name='Url')
    last_modified = models.DateTimeField(blank=True, null=True,
                                    verbose_name='Last-modified')
    links = models.ManyToManyField("self", symmetrical=False,
                                    null=True, verbose_name='Links')
    scanner = models.ForeignKey(Scanner, null=False, verbose_name='Scanner')

    def __unicode__(self):
        """Return the URL and last modified date."""
        return "<%s %s>" % (self.url, self.last_modified)


class Summary(models.Model):

    """The necessary configuration for summary reports."""

    name = models.CharField(max_length=256, unique=True, null=False,
                            verbose_name='Navn')
    description = models.TextField(verbose_name='Beskrivelse', null=True,
                                   blank=True)
    schedule = RecurrenceField(max_length=1024,
                               verbose_name='Planlagt afvikling')
    last_run = models.DateTimeField(blank=True, null=True,
                                      verbose_name='Sidste kørsel')
    recipients = models.ManyToManyField(UserProfile, null=True, blank=True,
                                        verbose_name="Modtagere")
    scanners = models.ManyToManyField(Scanner, null=True, blank=True,
                                      verbose_name="Scannere")
    organization = models.ForeignKey(Organization, null=False,
                                     verbose_name='Organisation')
    group = models.ForeignKey(Group, null=True, blank=True,
                                     verbose_name='Gruppe')
    do_email_recipients = models.BooleanField(default=False,
                                              verbose_name="Udsend mails")

    def __unicode__(self):
        """Return the name as a text representation of this summary object."""
        return self.name

    @property
    def display_name(self):
        """Display name = name."""
        return self.name

    class Meta:
        ordering = ['name', ]


class MD5Sum(models.Model):

    """"Store MD5 sums of binary files to avoid reprocessing."""

    organization = models.ForeignKey(Organization,
                                     null=False,
                                     verbose_name='Organisation')
    md5 = models.CharField(max_length=32, null=False, blank=False)
    is_cpr_scan = models.BooleanField()
    is_check_mod11 = models.BooleanField()
    is_ignore_irrelevant = models.BooleanField()

    class Meta:
        unique_together = ('md5', 'is_cpr_scan', 'is_check_mod11',
                        'is_ignore_irrelevant', 'organization')

    def __unicode__(self):
        return "{0}: {1}".format(self.organization.name, self.md5)
