# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-06-14 09:28
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('spellbook', '0007_auto_20160613_2312'),
    ]

    operations = [
        migrations.AddField(
            model_name='block',
            name='start_date',
            field=models.DateField(default=datetime.datetime(2016, 6, 14, 19, 28, 7, 792845)),
        ),
    ]
