# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-03-20 13:19
from __future__ import unicode_literals

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('studygroups', '0090_init_uuids'),
    ]

    operations = [
        migrations.AlterField(
            model_name='application',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AlterField(
            model_name='studygroup',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
