from django.db import models
from django.contrib.auth.models import User


class Permissions(models.Model):
    @classmethod
    def from_user(cls, user: User):
        return {
            "user": user.pk if user.is_authenticated else None,
            "anonymous": user.is_anonymous,
            "authenticated": user.is_authenticated,
            "staff": user.is_staff,
            "admin": user.is_superuser,
        }
