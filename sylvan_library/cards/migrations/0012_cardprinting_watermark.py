# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-12-22 11:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("cards", "0011_auto_20171222_1818")]

    operations = [
        migrations.AddField(
            model_name="cardprinting",
            name="watermark",
            field=models.CharField(blank=True, max_length=100, null=True),
        )
    ]
