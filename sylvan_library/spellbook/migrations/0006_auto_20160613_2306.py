# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-06-13 13:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('spellbook', '0005_auto_20160613_2305'),
    ]

    operations = [
        migrations.AlterField(
            model_name='set',
            name='code',
            field=models.CharField(max_length=10, unique=True),
        ),
    ]