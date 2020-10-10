# Generated by Django 2.2.13 on 2020-10-01 23:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("cards", "0108_add_model_dfc_layout")]

    operations = [
        migrations.AlterField(
            model_name="cardprinting",
            name="frame_effect",
            field=models.CharField(
                blank=True,
                choices=[
                    ("colorshifted", "colorshifted"),
                    ("companion", "Companion"),
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
                    ("waxingandwaningmoondfc", "Waxing and Waning Moon DFC"),
                    ("fullart", "Full Art"),
                ],
                max_length=50,
                null=True,
            ),
        )
    ]
