from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

# Register your models here.

from .models import Organization, UserProfile, Domain, RegexRule, Scanner
from .models import Scan, Match, Url, ConversionQueueItem

ar = admin.site.register
classes = [Organization, Domain, RegexRule, Scanner, Scan, Match,
           Url, ConversionQueueItem]
map(ar, classes)

class ProfileInline(admin.TabularInline):
    model = UserProfile
    extra = 1

class MyUserAdmin(UserAdmin):
    inlines = [ProfileInline]
    can_delete = False

admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)
