from django.core.management.base import BaseCommand


def run():
    from app.kube import get_status_all

    get_status_all()


class Command(BaseCommand):
    help = "Run daemon."

    def handle(self, *_, **__):
        run()
