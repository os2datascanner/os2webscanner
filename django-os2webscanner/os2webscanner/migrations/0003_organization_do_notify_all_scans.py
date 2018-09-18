# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('os2webscanner', '0002_auto_20160401_0817'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='do_notify_all_scans',
            field=models.BooleanField(default=True),
        ),
    ]
