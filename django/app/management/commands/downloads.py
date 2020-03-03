from django.core.management.base import BaseCommand
import shutil
from django.utils import timezone
from pathlib import Path
from app.models import *
import os


def cron():
    limit = timezone.now()
    limit -= timezone.timedelta(hours=12)
    for d in Download.objects.filter(created_at__lte=limit):
        try:
            os.remove(Path(d.path))
        except:
            pass
        d.delete()


class Command(BaseCommand):
    help = "Cleans downloads."

    def handle(self, *_, **__):
        cron()
