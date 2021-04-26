# Generated by Django 3.1.3 on 2021-04-23 23:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("cards", "0002_card_image_overhaul")]

    operations = [
        migrations.RemoveField(
            model_name="cardprinting", name="scryfall_illustration_id"
        ),
        migrations.AddField(
            model_name="cardfaceprinting",
            name="scryfall_illustration_id",
            field=models.CharField(blank=True, max_length=36, null=True),
        ),
    ]
