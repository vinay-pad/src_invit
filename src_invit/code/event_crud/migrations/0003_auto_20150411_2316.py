# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('event_crud', '0002_auto_20150410_0013'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='timelike',
            unique_together=set([('user', 'time_pref')]),
        ),
    ]
