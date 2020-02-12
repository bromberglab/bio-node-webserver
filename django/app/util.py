import os
import random
from django.utils import timezone
from django.conf import settings
from rest_framework import permissions


class NoGuestPermission(permissions.BasePermission):
    """
    Global permission check for guests.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and not is_guest(request.user)


list_path = os.path.join(settings.BASE_DIR, "assets", "The_Oxford_3000.list")
with open(list_path, "r") as f:
    word_list = f.read()
    word_list = word_list.split(" ")


def random_word():
    return random.choice(word_list)


def random_words(k=3):
    return random.choices(word_list, k=k)


def default_name(*a, **kw):
    return " ".join(random_words())


def random_chars(k=16, allow_uppercase=False):
    import random
    import string

    chars = string.ascii_lowercase + string.digits
    if allow_uppercase:
        chars += string.ascii_uppercase

    return "".join(random.choices(chars, k=k))


def now():
    return timezone.now().astimezone(tz=settings.TZ)


def is_guest(user):
    if user.is_superuser:
        return False
    return user.has_perm("app.is_guest_user")


dtformat = "%Y-%m-%d %H:%M:%S"
