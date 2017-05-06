# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('event_crud', '0008_event_latest_activity'),
    ]

    operations = [
        migrations.AddField(
            model_name='location',
            name='phone_no',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='location',
            name='rating',
            field=models.TextField(null=True),
        ),
    ]
