# Generated by Django 3.1.3 on 2021-02-23 23:11

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="UpdateBlock",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "update_mode",
                    models.CharField(
                        choices=[
                            ("UPDATE", "Update"),
                            ("CREATE", "Create"),
                            ("DELETE", "Delete"),
                        ],
                        max_length=10,
                    ),
                ),
                ("name", models.CharField(max_length=100, unique=True)),
                ("release_date", models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name="UpdateCard",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "update_mode",
                    models.CharField(
                        choices=[
                            ("UPDATE", "Update"),
                            ("CREATE", "Create"),
                            ("DELETE", "Delete"),
                        ],
                        max_length=10,
                    ),
                ),
                ("scryfall_oracle_id", models.CharField(max_length=36, unique=True)),
                ("name", models.CharField(max_length=200)),
                ("field_data", models.JSONField()),
            ],
        ),
        migrations.CreateModel(
            name="UpdateCardFaceLocalisation",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "update_mode",
                    models.CharField(
                        choices=[
                            ("UPDATE", "Update"),
                            ("CREATE", "Create"),
                            ("DELETE", "Delete"),
                        ],
                        max_length=10,
                    ),
                ),
                ("language_code", models.CharField(max_length=100)),
                ("printing_scryfall_id", models.CharField(max_length=36)),
                ("face_name", models.CharField(max_length=200)),
                ("face_printing_uuid", models.CharField(max_length=36)),
                ("field_data", models.JSONField()),
            ],
        ),
        migrations.CreateModel(
            name="UpdateCardPrinting",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "update_mode",
                    models.CharField(
                        choices=[
                            ("UPDATE", "Update"),
                            ("CREATE", "Create"),
                            ("DELETE", "Delete"),
                        ],
                        max_length=10,
                    ),
                ),
                ("card_scryfall_oracle_id", models.CharField(max_length=36)),
                ("card_name", models.CharField(max_length=200)),
                ("scryfall_id", models.CharField(max_length=36, unique=True)),
                ("set_code", models.CharField(max_length=10)),
                ("field_data", models.JSONField()),
            ],
        ),
        migrations.CreateModel(
            name="UpdateSet",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "update_mode",
                    models.CharField(
                        choices=[
                            ("UPDATE", "Update"),
                            ("CREATE", "Create"),
                            ("DELETE", "Delete"),
                        ],
                        max_length=10,
                    ),
                ),
                ("set_code", models.CharField(max_length=20, unique=True)),
                ("field_data", models.JSONField()),
            ],
        ),
        migrations.CreateModel(
            name="UpdateCardRuling",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "update_mode",
                    models.CharField(
                        choices=[
                            ("UPDATE", "Update"),
                            ("CREATE", "Create"),
                            ("DELETE", "Delete"),
                        ],
                        max_length=10,
                    ),
                ),
                ("card_name", models.CharField(max_length=100)),
                ("scryfall_oracle_id", models.CharField(max_length=36)),
                ("ruling_date", models.DateField()),
                ("ruling_text", models.CharField(max_length=4000)),
            ],
            options={"unique_together": {("scryfall_oracle_id", "ruling_text")}},
        ),
        migrations.CreateModel(
            name="UpdateCardLocalisation",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "update_mode",
                    models.CharField(
                        choices=[
                            ("UPDATE", "Update"),
                            ("CREATE", "Create"),
                            ("DELETE", "Delete"),
                        ],
                        max_length=10,
                    ),
                ),
                ("language_code", models.CharField(max_length=100)),
                ("printing_scryfall_id", models.CharField(max_length=36)),
                ("card_name", models.CharField(max_length=200)),
                ("field_data", models.JSONField()),
            ],
            options={"unique_together": {("language_code", "printing_scryfall_id")}},
        ),
        migrations.CreateModel(
            name="UpdateCardLegality",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "update_mode",
                    models.CharField(
                        choices=[
                            ("UPDATE", "Update"),
                            ("CREATE", "Create"),
                            ("DELETE", "Delete"),
                        ],
                        max_length=10,
                    ),
                ),
                ("card_name", models.CharField(max_length=100)),
                ("scryfall_oracle_id", models.CharField(max_length=36)),
                ("format_name", models.CharField(max_length=100)),
                ("restriction", models.CharField(max_length=100)),
            ],
            options={
                "verbose_name_plural": "Update card legalities",
                "unique_together": {("scryfall_oracle_id", "format_name")},
            },
        ),
        migrations.CreateModel(
            name="UpdateCardFacePrinting",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "update_mode",
                    models.CharField(
                        choices=[
                            ("UPDATE", "Update"),
                            ("CREATE", "Create"),
                            ("DELETE", "Delete"),
                        ],
                        max_length=10,
                    ),
                ),
                ("scryfall_id", models.CharField(max_length=36)),
                ("scryfall_oracle_id", models.CharField(max_length=36)),
                ("card_name", models.CharField(max_length=200)),
                ("printing_uuid", models.CharField(max_length=36)),
                ("card_face_name", models.CharField(max_length=200)),
                ("side", models.CharField(blank=True, max_length=1, null=True)),
                ("field_data", models.JSONField()),
            ],
            options={"unique_together": {("printing_uuid", "side")}},
        ),
        migrations.CreateModel(
            name="UpdateCardFace",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "update_mode",
                    models.CharField(
                        choices=[
                            ("UPDATE", "Update"),
                            ("CREATE", "Create"),
                            ("DELETE", "Delete"),
                        ],
                        max_length=10,
                    ),
                ),
                ("scryfall_oracle_id", models.CharField(max_length=36)),
                ("name", models.CharField(max_length=200)),
                ("face_name", models.CharField(max_length=200)),
                ("side", models.CharField(blank=True, max_length=1, null=True)),
                ("field_data", models.JSONField()),
            ],
            options={"unique_together": {("scryfall_oracle_id", "side")}},
        ),
    ]
