# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-02-08 10:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("cards", "0021_auto_20180208_1805")]

    operations = [
        migrations.AddField(
            model_name="card",
            name="colour_count",
            field=models.IntegerField(default=0),
            preserve_default=False,
        )
    ]
