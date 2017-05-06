# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('event_crud', '0006_auto_20150412_0047'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='locked_location_pref_id',
            field=models.BigIntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='locked_time_pref_id',
            field=models.BigIntegerField(null=True),
        ),
    ]
