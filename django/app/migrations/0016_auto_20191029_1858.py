# Generated by Django 2.2.6 on 2019-10-29 18:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0015_auto_20191029_1840'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='dependencies',
            field=models.ManyToManyField(related_name='dependents', to='app.Job'),
        ),
        migrations.AddField(
            model_name='job',
            name='json_string',
            field=models.TextField(default='{}'),
        ),
    ]
