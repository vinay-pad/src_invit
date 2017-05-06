# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user_id', models.BigIntegerField(null=True)),
                ('auth_token', models.TextField()),
                ('auth_secret', models.TextField()),
                ('phone_no', models.TextField(unique=True)),
                ('device_id', models.BigIntegerField(null=True)),
                ('name', models.TextField()),
                ('sex', models.CharField(default=b'', max_length=6)),
                ('dob', models.DateField(null=True)),
                ('first_login', models.DateTimeField(null=True)),
                ('last_login', models.DateTimeField(auto_now=True, null=True)),
            ],
            options={
                'db_table': 'invitusers',
            },
        ),
    ]
