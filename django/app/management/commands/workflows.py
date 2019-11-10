from app.models import *
from django.core.management.base import BaseCommand


def cron():
    while True:
        workflow = Workflow.objects.filter(should_run=True, scheduled=False).first()
        if workflow is None:
            break

        workflow.run_workflow()


class Command(BaseCommand):
    help = "Runs workflows."

    def handle(self, *_, **__):
        cron()
