# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-08-23 11:52


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('studygroups', '0072_delete_location'),
    ]

    operations = [
        migrations.AddField(
            model_name='studygroup',
            name='latitude',
            field=models.DecimalField(decimal_places=6, max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name='studygroup',
            name='longitude',
            field=models.DecimalField(decimal_places=6, max_digits=9, null=True),
        ),
    ]
