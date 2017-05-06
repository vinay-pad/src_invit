# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0004_auto_20150502_0249'),
    ]

    operations = [
        migrations.AlterField(
            model_name='logincache',
            name='user_hash',
            field=models.TextField(unique=True),
        ),
    ]
