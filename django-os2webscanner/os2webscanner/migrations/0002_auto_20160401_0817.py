# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('os2webscanner', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='cpr_whitelist',
            field=models.TextField(default=b'', verbose_name=b'Godkendte CPR-numre', blank=True),
        ),
        migrations.AddField(
            model_name='scan',
            name='whitelisted_cprs',
            field=models.TextField(default=b'', max_length=4096, verbose_name=b'Godkendte CPR-numre', blank=True),
        ),
    ]
