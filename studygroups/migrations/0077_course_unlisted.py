# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-08-28 15:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('studygroups', '0076_auto_20170825_1019'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='unlisted',
            field=models.BooleanField(default=False),
        ),
    ]