# Generated by Django 3.1.3 on 2020-12-19 23:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_import', '0005_updatecardlegality'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='updatecardlegality',
            options={'verbose_name_plural': 'Update card legalities'},
        ),
        migrations.RenameField(
            model_name='updatecardprinting',
            old_name='uuid',
            new_name='scryfall_id',
        ),
    ]
