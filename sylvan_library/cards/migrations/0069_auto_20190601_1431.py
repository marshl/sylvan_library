# Generated by Django 2.2.1 on 2019-06-01 14:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("cards", "0068_deck_exclude_colours"),
    ]

    operations = [
        migrations.AlterField(
            model_name="deck",
            name="exclude_colours",
            field=models.ManyToManyField(
                blank=True, related_name="exclude_from_decks", to="cards.Colour"
            ),
        ),
        migrations.CreateModel(
            name="UserProps",
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
                ("unused_cards_seed", models.IntegerField(default=0)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
