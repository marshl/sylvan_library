# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-07-03 13:20
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cards', '0028_auto_20180225_1550'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='cardprinting',
            unique_together=set([]),
        ),
    ]