from app.models import Globals, Job
from django.core.management.base import BaseCommand
from django.db import transaction


def cron():
    glob = Globals().instance

    while True:
        for j in Job.objects.filter(should_notify=True):
            should_notify = False
            with transaction.atomic():
                j = Job.objects.get(pk=j.pk)
                if j.should_notify:
                    should_notify = True
                    j.should_notify = False
                    j.save()
            if should_notify:
                j.status_change()

        job = Job.objects.filter(scheduled=False, dependencies_met=True).first()
        if job is None:
            break

        job.run_job()


class Command(BaseCommand):
    help = "Runs jobs."

    def handle(self, *_, **__):
        cron()
