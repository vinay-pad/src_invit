# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('event_crud', '0005_auto_20150411_2332'),
    ]

    operations = [
        migrations.RenameField(
            model_name='event',
            old_name='locked_loc_pref_id',
            new_name='locked_location_pref_id',
        ),
    ]
