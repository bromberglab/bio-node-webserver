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


def check_filters():
    import requests
    from app.images import import_image
    from app.models import NodeImage
    from django.contrib.auth.models import User

    r = requests.get(
        "https://api.github.com/repos/bromberglab/bio-node-filters/commits"
    ).json()
    sha = r[0]["sha"]
    r = requests.get(
        "https://api.github.com/repos/bromberglab/bio-node-filters/commits/%s" % sha
    ).json()
    tree = r["commit"]["tree"]["sha"]
    r = requests.get(
        "https://api.github.com/repos/bromberglab/bio-node-filters/git/trees/%s" % tree
    ).json()
    files = r["tree"]

    files = [f["path"] for f in files]
    files = list(filter(lambda f: "." not in f, files))

    admin = User.objects.get(username="admin")
    for f in files:
        image = "bromberglab/bio-node-filter.%s" % f
        try:
            NodeImage.objects.get(name=image)
            continue
        except:
            pass
        import_image(image, user=admin)


dtformat = "%Y-%m-%d %H:%M:%S"
