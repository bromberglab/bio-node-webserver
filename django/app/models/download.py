from django.db import models


class Download(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    path = models.TextField(default="")

