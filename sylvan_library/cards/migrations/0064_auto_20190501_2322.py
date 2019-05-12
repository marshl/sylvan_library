# Generated by Django 2.2 on 2019-05-01 23:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("cards", "0063_auto_20190501_2104")]

    operations = [
        migrations.AlterField(
            model_name="deckcard",
            name="board",
            field=models.CharField(
                choices=[
                    ("main", "Main"),
                    ("side", "Side"),
                    ("maybe", "Maybe"),
                    ("acquire", "Acquire"),
                ],
                default="main",
                max_length=20,
            ),
        )
    ]
