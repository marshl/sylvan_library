# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-01-24 11:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("cards", "0018_cardprinting_is_starter")]

    operations = [
        migrations.AlterField(
            model_name="cardprintinglanguage",
            name="physical_cards",
            field=models.ManyToManyField(
                related_name="printed_languages", to="cards.PhysicalCard"
            ),
        )
    ]
