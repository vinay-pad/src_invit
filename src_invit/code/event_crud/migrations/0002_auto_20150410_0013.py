# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('event_crud', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='locationlike',
            name='event',
            field=models.ForeignKey(default='', to='event_crud.Event'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='timelike',
            name='event',
            field=models.ForeignKey(default='', to='event_crud.Event'),
            preserve_default=False,
        ),
    ]
