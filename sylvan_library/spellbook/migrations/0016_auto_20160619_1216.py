# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-06-19 02:16
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('spellbook', '0015_rarity'),
    ]

    operations = [
        migrations.RenameField(
            model_name='rarity',
            old_name='order',
            new_name='display_order',
        ),
    ]
