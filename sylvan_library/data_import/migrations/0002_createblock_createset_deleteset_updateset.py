# Generated by Django 3.1.3 on 2020-12-02 22:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_import', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CreateBlock',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('release_date', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='CreateSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('set_code', models.CharField(max_length=20)),
                ('field_data', models.JSONField()),
            ],
        ),
        migrations.CreateModel(
            name='DeleteSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('set_code', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='UpdateSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('set_code', models.CharField(max_length=20)),
                ('field_data', models.JSONField()),
            ],
        ),
    ]
