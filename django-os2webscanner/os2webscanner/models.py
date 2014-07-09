# encoding: utf-8

"""Contains Django models for the Webscanner."""

import os
from subprocess import Popen
import re
from django.db import models
from django.contrib.auth.models import User
from recurrence.fields import RecurrenceField

from .utils import notify_user


# Sensitivity values
class Sensitivity:

    """Name space for sensitivity values."""

    HIGH = 2
    LOW = 1
    OK = 0

    choices = (
        (OK, 'Grøn'),
        (LOW, 'Gul'),
        (HIGH, 'Rød'),
    )


class Organization(models.Model):

    """Represents the organization for each user and scanner, etc.

    Users can only see material related to their own organization.
    """

    name = models.CharField(max_length=256, unique=True, verbose_name='Navn')
    contact_email = models.CharField(max_length=256, verbose_name='Email')
    contact_phone = models.CharField(max_length=256, verbose_name='Telefon')

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
                             related_name='user_profile',
                             verbose_name='Bruger')

    def __unicode__(self):
        """Return the user's username."""
        return self.user.username


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
                                     verbose_name='Organisation')
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
        if (not self.url.startswith('http://') and not
            self.url.startswith('https://')):
            return 'http://%s/' % self.url
        else:
            return self.url

    @property
    def sitemap_full_path(self):
        """Get the absolute path to the uploaded sitemap.xml file."""
        from django.conf import settings
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
    match_string = models.CharField(max_length=1024, blank=False,
                                    verbose_name='Udtryk')

    description = models.TextField(verbose_name='Beskrivelse')
    sensitivity = models.IntegerField(choices=Sensitivity.choices,
                                      default=Sensitivity.HIGH,
                                      verbose_name='Følsomhed')

    @property
    def display_name(self):
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
    schedule = RecurrenceField(max_length=1024,
                               verbose_name='Planlagt afvikling')
    whitelisted_names = models.TextField(max_length=4096, blank=True,
                                         default="",
                                         verbose_name='Godkendte navne')
    domains = models.ManyToManyField(Domain, related_name='scanners',
                                     null=False, verbose_name='Domæner')
    do_cpr_scan = models.BooleanField(default=True, verbose_name='CPR')
    do_name_scan = models.BooleanField(default=True, verbose_name='Navn')
    do_ocr = models.BooleanField(default=True, verbose_name='Scan billeder?')
    regex_rules = models.ManyToManyField(RegexRule,
                                         blank=True,
                                         null=True,
                                         verbose_name='Regex regler')

    @property
    def display_name(self):
        return "Scanner '%s'" % self.name

    @property
    def schedule_description(self):
        f = lambda s: "Schedule: " + s
        return f

    @property
    def has_active_scans(self):
        active_scanners = Scan.objects.filter(scanner=self, status__in=(
                        Scan.NEW, Scan.STARTED)).count()
        return active_scanners > 0

    def get_absolute_url(self):
        return '/scanners/'

    def __unicode__(self):
        return self.name

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
        try:
            process = Popen([os.path.join(SCRAPY_WEBSCANNER_DIR, "run.sh"),
                         str(scan.pk)], cwd=SCRAPY_WEBSCANNER_DIR)
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

    scanner = models.ForeignKey(Scanner, null=False, verbose_name='Scanner')
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
        """Returns a display text for the scan's status. Relies on the
        restriction that the status must be one of the allowed values."""
        text = [t for s, t in Scan.status_choices if self.status == s][0]
        return text

    # Reason for failure
    reason = models.CharField(max_length=1024, blank=True, default="",
                              verbose_name='Årsag')
    pid = models.IntegerField(null=True, blank=True, verbose_name='Pid')

    def __unicode__(self):
        """Return the name of the scan's scanner."""
        return "SCAN: " + self.scanner.name

    def save(self, *args, **kwargs):
        # Pre-save stuff
        super(Scan, self).save(*args, **kwargs)
        # Post-save stuff

        if (self.status in [Scan.DONE, Scan.FAILED] and
            (self._old_status != self.status)):
            # Send email
            notify_user(self)
            self._old_status = self.status

    def __init__(self, *args, **kwargs):
        super(Scan, self).__init__(*args, **kwargs)
        self._old_status = self.status


class Url(models.Model):

    """A representation of an actual URL on a domain with its MIME type."""

    url = models.CharField(max_length=2048, verbose_name='Url')
    mime_type = models.CharField(max_length=256, verbose_name='Mime-type')
    scan = models.ForeignKey(Scan, null=False, verbose_name='Scan')

    def __unicode__(self):
        """Return the URL."""
        return self.url


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
