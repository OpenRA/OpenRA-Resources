# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2023-02-05 13:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('openra', '0014_engines'),
    ]

    operations = [
        migrations.AddField(
            model_name='engines',
            name='is_playtest',
            field=models.BooleanField(default=False),
        ),
    ]
