from django.db import models


class CronJob(models.Model):
    name = models.CharField(max_length=20, primary_key=True)
    last_ran = models.DateTimeField()
