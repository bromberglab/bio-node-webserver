# Generated by Django 2.2.8 on 2020-01-20 01:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0044_auto_20200120_0116'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobretries',
            name='n',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]