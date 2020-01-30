from django.db import models
from django.contrib.auth.models import User
from app.util import random_chars


def new_token():
    return random_chars(32, allow_uppercase=True)


class ApiToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(
        max_length=32, primary_key=True, default=new_token, editable=False
    )
