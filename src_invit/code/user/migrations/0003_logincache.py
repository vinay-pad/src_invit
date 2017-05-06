# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_auto_20150414_2043'),
    ]

    operations = [
        migrations.CreateModel(
            name='LoginCache',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user_hash', models.TextField()),
                ('user_id', models.BigIntegerField(unique=True)),
            ],
        ),
    ]
