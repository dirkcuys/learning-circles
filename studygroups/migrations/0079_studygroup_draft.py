# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-02-01 13:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('studygroups', '0078_auto_20180109_1228'),
    ]

    operations = [
        migrations.AddField(
            model_name='studygroup',
            name='draft',
            field=models.BooleanField(default=True),
        ),
    ]