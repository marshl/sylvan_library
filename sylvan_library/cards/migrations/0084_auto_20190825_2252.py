# Generated by Django 2.2.1 on 2019-08-25 22:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("cards", "0083_cardprinting_is_alternative")]

    operations = [
        migrations.AddField(
            model_name="cardprinting",
            name="is_arena",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="cardprinting",
            name="is_mtgo",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="cardprinting",
            name="is_online_only",
            field=models.BooleanField(default=False),
        ),
    ]
