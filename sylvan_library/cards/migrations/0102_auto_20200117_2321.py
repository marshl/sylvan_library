# Generated by Django 2.2.8 on 2020-01-17 23:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("cards", "0101_auto_20191226_1612")]

    operations = [
        migrations.AlterField(
            model_name="cardprinting",
            name="frame_effect",
            field=models.CharField(
                blank=True,
                choices=[
                    ("colorshifted", "colorshifted"),
                    ("compasslanddfc", "compasslanddfc"),
                    ("devoid", "devoid"),
                    ("draft", "draft"),
                    ("extendedart", "extendedart"),
                    ("inverted", "inverted"),
                    ("legendary", "legendary"),
                    ("miracle", "miracle"),
                    ("mooneldrazidfc", "mooneldrazidfc"),
                    ("nyxborn", "nyxborn"),
                    ("nyxtouched", "nyxtouched"),
                    ("originpwdfc", "originpwdfc"),
                    ("showcase", "showcase"),
                    ("sunmoondfc", "sunmoondfc"),
                    ("tombstone", "tombstone"),
                ],
                max_length=50,
                null=True,
            ),
        )
    ]
