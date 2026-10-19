from django.db import migrations
from django.db.models import Value
from django.db.models.functions import Replace


def use_forward_slashes(apps, schema_editor):
    """
    Image paths saved on Windows use backslashes, which don't work on other systems.
    Forward slashes work everywhere.
    """
    CardImage = apps.get_model("cards", "CardImage")
    CardImage.objects.filter(file_path__contains="\\").update(
        file_path=Replace("file_path", Value("\\"), Value("/"))
    )


class Migration(migrations.Migration):

    dependencies = [
        ("cards", "0009_cardprinting_is_universes_beyond"),
    ]

    operations = [
        migrations.RunPython(use_forward_slashes, migrations.RunPython.noop),
    ]
