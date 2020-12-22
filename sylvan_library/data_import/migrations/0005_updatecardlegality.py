# Generated by Django 3.1.3 on 2020-12-19 19:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_import', '0004_updatecardruling'),
    ]

    operations = [
        migrations.CreateModel(
            name='UpdateCardLegality',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('update_mode', models.CharField(choices=[('UPDATE', 'Update'), ('CREATE', 'Create'), ('DELETE', 'Delete')], max_length=10)),
                ('card_name', models.CharField(max_length=100)),
                ('scryfall_oracle_id', models.CharField(max_length=36)),
                ('format_name', models.CharField(max_length=100)),
                ('restriction', models.CharField(max_length=100)),
            ],
            options={
                'unique_together': {('scryfall_oracle_id', 'format_name')},
            },
        ),
    ]
