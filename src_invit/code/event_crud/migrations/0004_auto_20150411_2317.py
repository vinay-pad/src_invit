# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('event_crud', '0003_auto_20150411_2316'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='locationlike',
            unique_together=set([('user', 'location_pref')]),
        ),
    ]
