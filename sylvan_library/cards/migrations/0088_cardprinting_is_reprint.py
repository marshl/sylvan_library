# Generated by Django 2.2.1 on 2019-08-29 19:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("cards", "0087_cardprinting_is_paper")]

    operations = [
        migrations.AddField(
            model_name="cardprinting",
            name="is_reprint",
            field=models.BooleanField(default=False),
        )
    ]