# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('event_crud', '0004_auto_20150411_2317'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='locked_loc_pref_id',
            field=models.BigIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='event',
            name='locked_time_pref_id',
            field=models.BigIntegerField(default=0),
            preserve_default=False,
        ),
    ]
