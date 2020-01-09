import os
import random
from django.utils import timezone
from django.conf import settings

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


def now():
    return timezone.now().astimezone(tz=settings.TZ)


dtformat = "%Y-%m-%d %H:%M:%S"
