# Generated by Django 2.2.9 on 2020-02-22 22:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("cardsearch", "0002_auto_20200222_1955")]

    operations = [
        migrations.AddField(
            model_name="cardsearchmetadata",
            name="symbol_count_generic",
            field=models.IntegerField(default=0),
        )
    ]