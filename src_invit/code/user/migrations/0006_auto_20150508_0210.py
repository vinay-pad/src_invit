# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0005_auto_20150502_2348'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='device_id',
            field=models.TextField(null=True),
        ),
    ]
