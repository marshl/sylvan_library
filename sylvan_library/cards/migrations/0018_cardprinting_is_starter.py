# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-12-31 08:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cards', '0017_cardprinting_release_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='cardprinting',
            name='is_starter',
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
    ]