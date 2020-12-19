# Generated by Django 3.1.3 on 2020-12-05 14:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_import', '0002_createblock_createset_deleteset_updateset'),
    ]

    operations = [
        migrations.CreateModel(
            name='UpdateBlock',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('update_mode', models.CharField(choices=[('UPDATE', 'Update'), ('CREATE', 'Create'), ('DELETE', 'Delete')], max_length=10)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('release_date', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='UpdateCardFacePrinting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('update_mode', models.CharField(choices=[('UPDATE', 'Update'), ('CREATE', 'Create'), ('DELETE', 'Delete')], max_length=10)),
                ('card_scryfall_oracle_id', models.CharField(max_length=36)),
                ('card_name', models.CharField(max_length=200)),
                ('printing_uuid', models.CharField(max_length=36)),
                ('card_face_name', models.CharField(max_length=200)),
                ('side', models.CharField(blank=True, max_length=1, null=True)),
            ],
            options={
                'unique_together': {('printing_uuid', 'side')},
            },
        ),
        migrations.DeleteModel(
            name='CreateBlock',
        ),
        migrations.DeleteModel(
            name='CreateCard',
        ),
        migrations.DeleteModel(
            name='CreateCardFace',
        ),
        migrations.DeleteModel(
            name='CreateCardFacePrinting',
        ),
        migrations.DeleteModel(
            name='CreateCardPrinting',
        ),
        migrations.DeleteModel(
            name='CreateSet',
        ),
        migrations.DeleteModel(
            name='DeleteCardFace',
        ),
        migrations.DeleteModel(
            name='DeleteCardPrinting',
        ),
        migrations.DeleteModel(
            name='DeleteSet',
        ),
        migrations.DeleteModel(
            name='DestroyCard',
        ),
        migrations.AddField(
            model_name='updatecard',
            name='update_mode',
            field=models.CharField(choices=[('UPDATE', 'Update'), ('CREATE', 'Create'), ('DELETE', 'Delete')], default='CREATE', max_length=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='updatecardface',
            name='update_mode',
            field=models.CharField(choices=[('UPDATE', 'Update'), ('CREATE', 'Create'), ('DELETE', 'Delete')], default='CREATE', max_length=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='updatecardprinting',
            name='set_code',
            field=models.CharField(default='CREATE', max_length=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='updatecardprinting',
            name='update_mode',
            field=models.CharField(choices=[('UPDATE', 'Update'), ('CREATE', 'Create'), ('DELETE', 'Delete')], default='CREATE', max_length=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='updateset',
            name='update_mode',
            field=models.CharField(choices=[('UPDATE', 'Update'), ('CREATE', 'Create'), ('DELETE', 'Delete')], default='CREATE', max_length=10),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='updatecard',
            name='scryfall_oracle_id',
            field=models.CharField(max_length=36, unique=True),
        ),
        migrations.AlterField(
            model_name='updatecardprinting',
            name='uuid',
            field=models.CharField(max_length=36, unique=True),
        ),
        migrations.AlterField(
            model_name='updateset',
            name='set_code',
            field=models.CharField(max_length=20, unique=True),
        ),
        migrations.AlterUniqueTogether(
            name='updatecardface',
            unique_together={('scryfall_oracle_id', 'side')},
        ),
    ]