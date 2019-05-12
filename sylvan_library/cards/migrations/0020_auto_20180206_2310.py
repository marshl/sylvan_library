# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-02-06 12:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("cards", "0019_auto_20180124_2207")]

    operations = [
        migrations.CreateModel(
            name="Colour",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("symbol", models.CharField(max_length=1, unique=True)),
                ("name", models.CharField(max_length=15, unique=True)),
                ("display_order", models.IntegerField(unique=True)),
            ],
        ),
        migrations.RemoveField(model_name="card", name="colour"),
        migrations.RemoveField(model_name="card", name="colour_identity"),
        migrations.AddField(
            model_name="card",
            name="colour",
            field=models.ManyToManyField(
                related_name="colour_cards", to="cards.Colour"
            ),
        ),
        migrations.AddField(
            model_name="card",
            name="colour_identity",
            field=models.ManyToManyField(
                related_name="colour_id_cards", to="cards.Colour"
            ),
        ),
    ]
