# Generated by Django 2.2.8 on 2020-02-24 18:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0057_auto_20200224_1826'),
    ]

    operations = [
        migrations.AlterField(
            model_name='apiworkflow',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='apiworkflow',
            name='run_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]