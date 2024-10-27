# Generated by Django 4.2.16 on 2024-10-27 21:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("cards", "0006_increase_cardface_text_length"),
    ]

    operations = [
        migrations.AddField(
            model_name="cardprice",
            name="cheapest_card",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="cheapest_price",
                to="cards.card",
            ),
        ),
    ]
