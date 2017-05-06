# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.TextField()),
                ('status', models.CharField(max_length=10)),
                ('muted', models.BooleanField(default=False)),
                ('created_ts', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('place_id', models.TextField()),
                ('name', models.TextField()),
                ('address', models.TextField()),
                ('latitude', models.DecimalField(null=True, max_digits=12, decimal_places=9, blank=True)),
                ('longitude', models.DecimalField(null=True, max_digits=12, decimal_places=9, blank=True)),
                ('service', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='LocationLike',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_ts', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='LocationPreference',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_ts', models.DateTimeField()),
                ('locked', models.BooleanField(default=False)),
                ('event', models.ForeignKey(to='event_crud.Event')),
                ('location', models.ForeignKey(to='event_crud.Location')),
                ('user', models.ForeignKey(to='user.User')),
            ],
        ),
        migrations.CreateModel(
            name='Time',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('event_start_time', models.DateTimeField()),
                ('event_end_time', models.DateTimeField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='TimeLike',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_ts', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='TimePreference',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_ts', models.DateTimeField()),
                ('locked', models.BooleanField(default=False)),
                ('event', models.ForeignKey(to='event_crud.Event')),
                ('time', models.ForeignKey(to='event_crud.Time')),
                ('user', models.ForeignKey(to='user.User')),
            ],
        ),
        migrations.AddField(
            model_name='timelike',
            name='time_pref',
            field=models.ForeignKey(to='event_crud.TimePreference'),
        ),
        migrations.AddField(
            model_name='timelike',
            name='user',
            field=models.ForeignKey(to='user.User'),
        ),
        migrations.AddField(
            model_name='locationlike',
            name='location_pref',
            field=models.ForeignKey(to='event_crud.LocationPreference'),
        ),
        migrations.AddField(
            model_name='locationlike',
            name='user',
            field=models.ForeignKey(to='user.User'),
        ),
        migrations.AlterUniqueTogether(
            name='location',
            unique_together=set([('place_id', 'service')]),
        ),
        migrations.AddField(
            model_name='event',
            name='location_preference',
            field=models.ManyToManyField(to='event_crud.Location', through='event_crud.LocationPreference'),
        ),
        migrations.AddField(
            model_name='event',
            name='owner',
            field=models.ForeignKey(related_name='owner', to='user.User'),
        ),
        migrations.AddField(
            model_name='event',
            name='participants',
            field=models.ManyToManyField(related_name='participant', to='user.User'),
        ),
        migrations.AddField(
            model_name='event',
            name='time_preference',
            field=models.ManyToManyField(to='event_crud.Time', through='event_crud.TimePreference'),
        ),
    ]
