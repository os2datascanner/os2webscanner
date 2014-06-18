from django.contrib import admin

# Register your models here.

from .models import Organization, UserProfile, Domain, RegexRule, Scanner
from .models import Scan, Match, Url, ConversionQueueItem

ar = admin.site.register
classes = [Organization, UserProfile, Domain, RegexRule, Scanner, Scan, Match,
           Url, ConversionQueueItem]
map(ar, classes)
