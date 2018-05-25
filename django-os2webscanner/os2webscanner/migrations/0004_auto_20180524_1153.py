# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('os2webscanner', '0003_organization_do_notify_all_scans'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scan',
            name='do_cpr_ignore_irrelevant',
            field=models.BooleanField(default=True, verbose_name=b'Ignorer ugyldige f\xc3\xb8dselsdatoer'),
        ),
        migrations.AlterField(
            model_name='scan',
            name='do_cpr_modulus11',
            field=models.BooleanField(default=True, verbose_name=b'Tjek modulus-11'),
        ),
        migrations.AlterField(
            model_name='scan',
            name='do_last_modified_check',
            field=models.BooleanField(default=True, verbose_name=b'Tjek Last-Modified'),
        ),
        migrations.AlterField(
            model_name='scan',
            name='do_link_check',
            field=models.BooleanField(default=False, verbose_name=b'Tjek links'),
        ),
        migrations.AlterField(
            model_name='scanner',
            name='do_cpr_ignore_irrelevant',
            field=models.BooleanField(default=True, verbose_name=b'Ignorer ugyldige f\xc3\xb8dselsdatoer'),
        ),
        migrations.AlterField(
            model_name='scanner',
            name='do_cpr_modulus11',
            field=models.BooleanField(default=True, verbose_name=b'Tjek modulus-11'),
        ),
        migrations.AlterField(
            model_name='scanner',
            name='do_last_modified_check',
            field=models.BooleanField(default=True, verbose_name=b'Tjek Last-Modified'),
        ),
        migrations.AlterField(
            model_name='scanner',
            name='do_link_check',
            field=models.BooleanField(default=False, verbose_name=b'Tjek links'),
        ),
    ]
