# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0003_logincache'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='logincache',
            name='id',
        ),
        migrations.AlterField(
            model_name='logincache',
            name='user_id',
            field=models.BigIntegerField(serialize=False, primary_key=True),
        ),
    ]
