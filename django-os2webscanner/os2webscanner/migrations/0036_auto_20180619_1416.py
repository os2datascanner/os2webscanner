# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-06-19 12:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('os2webscanner', '0035_merge_20180614_0957'),
    ]

    operations = [
        migrations.AlterField(
            model_name='match',
            name='matched_data',
            field=models.CharField(max_length=4096, verbose_name='Data match'),
        ),
    ]
