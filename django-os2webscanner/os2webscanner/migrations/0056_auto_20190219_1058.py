# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-02-19 09:58
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('os2webscanner', '0055_auto_20190214_1543'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='exchangescan',
            name='scan_ptr',
        ),
        migrations.RemoveField(
            model_name='filescan',
            name='scan_ptr',
        ),
        migrations.DeleteModel(
            name='ExchangeScan',
        ),
        migrations.DeleteModel(
            name='FileScan',
        ),
    ]
