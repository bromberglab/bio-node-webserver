# Generated by Django 2.2.8 on 2020-02-12 16:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0053_upload_size'),
    ]

    operations = [
        migrations.AddField(
            model_name='globals',
            name='drained',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='globals',
            name='should_expand',
            field=models.BooleanField(default=False),
        ),
    ]