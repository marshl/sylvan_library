# Generated by Django 3.1.3 on 2020-12-06 16:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cards', '0003_auto_20201205_1440'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='deckcard',
            options={'ordering': ['card__converted_mana_cost', 'card__name']},
        ),
        migrations.RemoveField(
            model_name='card',
            name='colour_sort_key',
        ),
    ]
