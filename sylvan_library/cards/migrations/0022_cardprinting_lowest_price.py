# Generated by Django 3.1.3 on 2021-01-15 23:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cards', '0021_auto_20210112_2311'),
    ]

    operations = [
        migrations.AddField(
            model_name='cardprinting',
            name='lowest_price',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='lowest_price_printing', to='cards.cardprice'),
        ),
    ]
