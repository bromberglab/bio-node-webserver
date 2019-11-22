# Generated by Django 2.2.6 on 2019-11-22 17:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0024_globals_some_uuid'),
    ]

    operations = [
        migrations.AddField(
            model_name='nodeimage',
            name='imported',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='nodeimage',
            name='imported_tag',
            field=models.CharField(blank=True, default='', max_length=128),
        ),
    ]