from django.core.management.base import BaseCommand
import shutil
from django.utils import timezone
from pathlib import Path
from app.models import Upload, Job
from app.files import list_dirs, base_path


def cron():
    limit = timezone.now()
    limit -= timezone.timedelta(hours=48)
    for d in Upload.objects.filter(is_finished=False, started_at__lte=limit):
        d.delete()

    n = 0
    for typedir in list_dirs(base_path):
        for uploaddir in list_dirs(base_path / typedir):
            try:
                upload = Upload.objects.get(uuid=uploaddir)
                continue
            except:
                pass
            try:
                job = Job.objects.get(uuid=uploaddir)
                if not job.finished:
                    if job.workflow is None or not job.workflow.finished:
                        continue
            except:
                pass
            shutil.rmtree(str(base_path / typedir / uploaddir))
            n += 1
    if n > 0:
        print("Removed %d stale uploads." % n)


class Command(BaseCommand):
    help = "Cleans uploads."

    def handle(self, *_, **__):
        cron()
