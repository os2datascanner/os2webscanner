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

import os
import shutil
from subprocess import Popen
import re
import datetime
import json

from django.db import models
from django.contrib.auth.models import User
from recurrence.fields import RecurrenceField

from os2webscanner.utils import notify_user
from django.conf import settings


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
    do_use_groups = models.BooleanField(default=False)

    def __unicode__(self):
        """Return the name of the organization."""
        return self.name


class UserProfile(models.Model):

    """OS2 Web Scanner specific user profile.

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
                               verbose_name='Sitemap')

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
        return "%s/%s" % (settings.BASE_DIR, self.sitemap.url)

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
    group = models.ForeignKey(Group, null=True,
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
    group = models.ForeignKey(Group, null=True,
                                     verbose_name='Gruppe')
    schedule = RecurrenceField(max_length=1024,
                               verbose_name='Planlagt afvikling')
    whitelisted_names = models.TextField(max_length=4096, blank=True,
                                         default="",
                                         verbose_name='Godkendte navne')
    domains = models.ManyToManyField(Domain, related_name='scanners',
                                     null=False, verbose_name='Domæner')
    do_cpr_scan = models.BooleanField(default=True, verbose_name='CPR')
    do_name_scan = models.BooleanField(default=False, verbose_name='Navn')
    do_ocr = models.BooleanField(default=False, verbose_name='Scan billeder?')
    do_cpr_modulus11 = models.BooleanField(default=True,
                                           verbose_name='Check modulus-11')
    do_link_check = models.BooleanField(default=False,
                                        verbose_name='Linkcheck')
    do_external_link_check = models.BooleanField(default=False,
                                                 verbose_name='Check ' +
                                                              'externe links')
    do_last_modified_check = models.BooleanField(default=True,
                                                 verbose_name='Check ' +
                                                              'Last-Modified')
    do_last_modified_check_head_request = \
        models.BooleanField(default=True, verbose_name='Brug HEAD request')
    regex_rules = models.ManyToManyField(RegexRule,
                                         blank=True,
                                         null=True,
                                         verbose_name='Regex regler')

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
        f = lambda s: "Schedule: " + s
        return f

    @property
    def has_active_scans(self):
        """Whether the scanner has active scans."""
        active_scanners = Scan.objects.filter(scanner=self, status__in=(
                        Scan.NEW, Scan.STARTED)).count()
        return active_scanners > 0

    def run(self, test_only=False):
        """Run a scan with the Scanner.

        Return the Scan object if we started the scanner.
        Return None if there is already a scanner running,
        or if there was a problem running the scanner.
        If test_only is True, only check if we can run a scan, don't actually
        run one.
        """
        if self.has_active_scans:
            return None
        # Create a new Scan
        scan = Scan(scanner=self, status=Scan.NEW)
        scan.save()
        # Get path to run script
        SCRAPY_WEBSCANNER_DIR = os.path.join(os.path.dirname(os.path.dirname(
            os.path.dirname(
                os.path.realpath(__file__)))), "scrapy-webscanner")

        if test_only:
            return scan

        if not os.path.exists(scan.scan_log_dir):
            os.makedirs(scan.scan_log_dir)
        log_file = open(scan.scan_log_file, "a")

        try:
            process = Popen([os.path.join(SCRAPY_WEBSCANNER_DIR, "run.sh"),
                             str(scan.pk)], cwd=SCRAPY_WEBSCANNER_DIR,
                            stderr=log_file,
                            stdout=log_file)
        except Exception as e:
            return None
        return scan

    def get_absolute_url(self):
        """Get the absolute URL for scanners."""
        return '/scanners/'

    def __unicode__(self):
        """Return the name of the scanner."""
        return self.name


class Scan(models.Model):

    """An actual instance of the scanning process done by a scanner."""

    scanner = models.ForeignKey(Scanner, null=False, verbose_name='Scanner',
                                related_name='scans')
    start_time = models.DateTimeField(blank=True, null=True,
                                      verbose_name='Starttidspunkt')
    end_time = models.DateTimeField(blank=True, null=True,
                                    verbose_name='Sluttidspunkt')

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

    def __unicode__(self):
        """Return the name of the scan's scanner."""
        return "SCAN: " + self.scanner.name

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
            notify_user(self)

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
    scan = models.ForeignKey(Scan, null=False, verbose_name='Scan')
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
    scan = models.ForeignKey(Scan, null=False, verbose_name='Scan')
    matched_data = models.CharField(max_length=1024, verbose_name='Data match')
    matched_rule = models.CharField(max_length=256, verbose_name='Regel match')
    sensitivity = models.IntegerField(choices=Sensitivity.choices,
                                      default=Sensitivity.HIGH,
                                      verbose_name='Følsomhed')

    def get_matched_rule_display(self):
        """Return a display name for the rule."""
        if self.matched_rule == 'cpr':
            return "CPR"
        elif self.matched_rule == 'name':
            return "Navn"
        else:
            return self.matched_rule

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
