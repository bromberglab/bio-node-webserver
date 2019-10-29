from django.core.management.base import BaseCommand, CommandError
from app.models import CronJob
from django.utils.timezone import now
from django.conf import settings
from datetime import datetime


def should_run(name, seconds_interval):
    try:
        c = CronJob.objects.get(name=name)
    except CronJob.DoesNotExist:
        CronJob(name=name, last_ran=now()).save()
        return True

    if (now() - c.last_ran).total_seconds() >= seconds_interval - 1:
        c.last_ran = now()
        c.save()
        return True

    return False


class CronTask:
    def __init__(self, name, seconds_interval, function):
        self.name = name
        self.seconds_interval = seconds_interval
        self.function = function


def cron_worker():
    from .images import cron as images_cron
    from .jobs import cron as jobs_cron
    from .workflows import cron as workflows_cron

    seconds = 1
    minutes = 60 * seconds
    hours = 60 * minutes
    days = 24 * hours
    if not should_run("main", 5 * seconds):
        return

    tasks = [
        # CronTask("some_function", 10 * minutes, some_function),
        # ...
        CronTask("images_cron", 30 * seconds, images_cron),
        CronTask("workflows_cron", 5 * seconds, workflows_cron),
        CronTask("jobs_cron", 5 * seconds, jobs_cron),
    ]

    for task in tasks:
        if should_run(task.name, task.seconds_interval):
            task.function()


def cron():
    from threading import Thread
    Thread(target=cron_worker).start()


class Command(BaseCommand):
    help = 'Runs all required cron commands'

    def handle(self, *_, **__):
        cron_worker()
