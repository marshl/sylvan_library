# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-07-13 09:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('spellbook', '0023_remove_card_layout'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='layout',
            field=models.CharField(default='normal', max_length=20),
        ),
    ]
