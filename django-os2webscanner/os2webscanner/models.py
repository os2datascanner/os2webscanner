# encoding: utf-8
import re
from django.db import models
from django.contrib.auth.models import User


# Sensitivity values
class Sensitivity:
    """Name space for sensitivity values"""
    HIGH = 2
    LOW = 1
    OK = 0

    choices = (
        (OK, 'Grøn'),
        (LOW, 'Gul'),
        (HIGH, 'Rød'),
    )


class Organization(models.Model):
    """Represents the organization for each user and scanner, etc. Users can
    only see material related to their own organization."""
    name = models.CharField(max_length=256, unique=True)

    def __unicode__(self):
        return self.name


class UserProfile(models.Model):
    """OS2 Web Scanner specific user profile.
    Each user MUST be associated with an organization."""

    organization = models.ForeignKey(Organization, null=False)
    user = models.ForeignKey(User, unique=True, related_name='user_profile')

    def __unicode__(self):
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
        (ROBOTSTXT, 'Robots.txt'),
        (WEBSCANFILE, 'Webscan.html'),
        (METAFIELD, 'Meta-felt'),
    )

    url = models.CharField(max_length=2048)
    organization = models.ForeignKey(Organization, null=False)
    validation_status = models.IntegerField(choices=validation_choices,
                                            default=INVALID)
    validation_method = models.IntegerField(choices=validation_method_choices,
                                            default=ROBOTSTXT)
    exclusion_rules = models.TextField(blank=True, default="")
    sitemap = models.FileField(upload_to='sitemaps', blank=True)

    def exclusion_rule_list(self):
        """Return the exclusion rules as a list of strings or regex objects"""
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
        if (not self.url.startswith('http://') and not
                self.url.startswith('https://')):
            return 'http://%s/' % self.url
        else:
            return self.url

    @property
    def sitemap_full_path(self):
        from django.conf import settings
        return "%s/%s" % (settings.BASE_DIR, self.sitemap.url)

    def get_absolute_url(self):
        return '/domains/'

    def __unicode__(self):
        return self.url


class RegexRule(models.Model):
    """Represents matching rules based on regular expressions."""

    name = models.CharField(max_length=256, unique=True, null=False)
    organization = models.ForeignKey(Organization, null=False)
    match_string = models.CharField(max_length=1024, blank=False)

    description = models.TextField()
    sensitivity = models.IntegerField(choices=Sensitivity.choices,
                                      default=Sensitivity.HIGH)

    def get_absolute_url(self):
        return '/rules/'

    def __unicode__(self):
        return self.name


class Scanner(models.Model):
    """A scanner, i.e. a template for actual scanning jobs."""
    name = models.CharField(max_length=256, unique=True, null=False)
    organization = models.ForeignKey(Organization, null=False)
    schedule = models.CharField(max_length=1024)
    whitelisted_names = models.TextField(max_length=4096, blank=True,
                                         default="")
    domains = models.ManyToManyField(Domain, related_name='scanners',
                                     null=False)
    do_cpr_scan = models.BooleanField(default=True)
    do_name_scan = models.BooleanField(default=True)
    regex_rules = models.ManyToManyField(RegexRule, blank=True, null=True)

    @property
    def schedule_description(self):
        f = lambda s: "Schedule: " + s
        return f

    def get_absolute_url(self):
        return '/scanners/'

    def __unicode__(self):
        return self.name


class Scan(models.Model):
    """An actual instance of the scanning process done by a scanner."""

    scanner = models.ForeignKey(Scanner, null=False)
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)

    # Scan status
    NEW = "NEW"
    STARTED = "STARTED"
    DONE = "DONE"
    FAILED = "FAILED"

    status_choices = (
        (NEW, "Ny"),
        (STARTED, "I gang"),
        (DONE, "Afsluttet"),
        (FAILED, "Fejlet"),
    )
    status = models.CharField(max_length=10, choices=status_choices,
                              default=NEW)
    # Reason for failure
    reason = models.CharField(max_length=1024, blank=True, default="")
    pid = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return "SCAN: " + self.scanner.name


class Url(models.Model):
    """A representation of an actual URL on a domain with its MIME type."""
    url = models.CharField(max_length=2048)
    mime_type = models.CharField(max_length=256)  # TODO: Use choices/codes?
    scan = models.ForeignKey(Scan, null=False)

    def __unicode__(self):
        return self.url


class Match(models.Model):
    """The data associated with a single match in a single URL."""
    url = models.ForeignKey(Url, null=False)
    scan = models.ForeignKey(Scan, null=False)
    matched_data = models.CharField(max_length=1024)
    matched_rule = models.CharField(max_length=256)  # Name of matching rule.
    sensitivity = models.IntegerField(choices=Sensitivity.choices,
                                      default=Sensitivity.HIGH)

    def get_matched_rule_display(self):
        if self.matched_rule == 'cpr':
            return "CPR"
        elif self.matched_rule == 'name':
            return "Navn"
        else:
            return self.matched_rule

    def get_sensitivity_class(self):
        if self.sensitivity == Sensitivity.HIGH:
            return "danger"
        elif self.sensitivity == Sensitivity.LOW:
            return "warning"
        elif self.sensitivity == Sensitivity.OK:
            return "success"

    def __unicode__(self):
        return u"Match: %s; [%s] %s <%s>" % (self.get_sensitivity_display(),
                                             self.matched_rule,
                                             self.matched_data, self.url)


class ConversionQueueItem(models.Model):
    """Represents an item in the conversion queue."""
    file = models.CharField(max_length=4096)
    type = models.CharField(max_length=256)  # We may want to specify choices
    url = models.ForeignKey(Url, null=False)

    # Note that SUCCESS is indicated by just deleting the record
    NEW = "NEW"
    PROCESSING = "PROCESSING"
    FAILED = "FAILED"
    SUCCEEDED = "SUCCEEDED"

    status_choices = (
        (NEW, "Ny"),
        (PROCESSING, "I gang"),
        (FAILED, "Fejlet"),
        (SUCCEEDED, "Success")
    )
    status = models.CharField(max_length=10, choices=status_choices,
                              default=NEW)

    process_id = models.IntegerField(blank=True, null=True)
    process_start_time = models.DateTimeField(blank=True, null=True)

    @property
    def file_path(self):
        return self.file
