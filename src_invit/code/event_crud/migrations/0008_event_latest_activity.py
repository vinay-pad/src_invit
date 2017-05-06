# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('event_crud', '0007_auto_20150412_0105'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='latest_activity',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
    ]
