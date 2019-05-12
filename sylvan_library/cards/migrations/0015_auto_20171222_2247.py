# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-12-22 11:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("cards", "0014_auto_20171222_2238")]

    operations = [
        migrations.AddField(
            model_name="card",
            name="hand_modifier",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="card",
            name="life_modifier",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
