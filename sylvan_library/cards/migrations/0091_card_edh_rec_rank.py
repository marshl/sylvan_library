# Generated by Django 2.2.1 on 2019-09-01 19:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("cards", "0090_cardprice")]

    operations = [
        migrations.AddField(
            model_name="card", name="edh_rec_rank", field=models.IntegerField(default=0)
        )
    ]
