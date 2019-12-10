from django.core.management.base import BaseCommand
from app.models import *
from app.kube import get_resources
import re

reg = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}(-\d+)?-.{5}$"


def cron():
    res = get_resources()
    for k, v in res.items():
        if re.match(reg, k):
            ResourceUsage.update(k, *v)


class Command(BaseCommand):
    help = "Updates resources."

    def handle(self, *_, **__):
        cron()
