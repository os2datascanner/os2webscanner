from django.contrib import admin

from .models.roles.remediator_model import Remediator
from .models.roles.defaultrole_model import DefaultRole
from .models.aliases.adsidalias_model import ADSIDAlias
from .models.aliases.emailalias_model import EmailAlias
from .models.documentreport_model import DocumentReport

# Register your models here.

admin.site.register(DocumentReport)

@admin.register(ADSIDAlias)
class ADSIDAliasAdmin(admin.ModelAdmin):
    list_display = ('sid', 'user', )

@admin.register(EmailAlias)
class EmailAliasAdmin(admin.ModelAdmin):
    list_display = ('address', 'user', )

@admin.register(DefaultRole)
class DefaultRoleAdmin(admin.ModelAdmin):
    list_display = ('user', )

@admin.register(Remediator)
class RemediatorAdmin(admin.ModelAdmin):
    list_display = ('user', )
