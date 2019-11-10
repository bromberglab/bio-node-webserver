from django.core.management.base import BaseCommand
from app.images import cron as img_cron


def cron():
    img_cron()


class Command(BaseCommand):
    help = "Gets images."

    def handle(self, *_, **__):
        cron()
