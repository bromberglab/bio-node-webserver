from app.models import *
from django.core.management.base import BaseCommand


def cron():
    glob = Globals().instance

    while True:
        job = Job.objects.filter(scheduled=False, dependencies_met=True).first()
        if job is None:
            break

        job.run_job()


class Command(BaseCommand):
    help = "Runs jobs."

    def handle(self, *_, **__):
        cron()
