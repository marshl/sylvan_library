# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-02-18 08:07
from __future__ import unicode_literals

import bitfield.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("cards", "0023_auto_20180218_1654")]

    operations = [
        migrations.RemoveField(model_name="card", name="colour_identities"),
        migrations.RemoveField(model_name="card", name="colours"),
        migrations.AlterField(
            model_name="card",
            name="colour_flags",
            field=bitfield.models.BitField(
                ("white", "blue", "black", "red", "green"), default=None
            ),
        ),
        migrations.AlterField(
            model_name="card",
            name="colour_identity_flags",
            field=bitfield.models.BitField(
                ("white", "blue", "black", "red", "green"), default=None
            ),
        ),
    ]
