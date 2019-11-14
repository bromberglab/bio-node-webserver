import shutil
from django.utils import timezone
from pathlib import Path
from app.models import *
import os


def cron():
    limit = timezone.now()
    limit -= timezone.timedelta(hours=2)
    for d in Download.objects.filter(created_at__lte=limit):
        os.remove(Path(d.path))
        d.delete()
