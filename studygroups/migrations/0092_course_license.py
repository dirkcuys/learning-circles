# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-04-10 07:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('studygroups', '0091_auto_20180320_1319'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='license',
            field=models.CharField(blank=True, max_length=128),
        ),
    ]