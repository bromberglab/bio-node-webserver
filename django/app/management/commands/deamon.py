from django.core.management.base import BaseCommand


def run():
    print("[Deamon]")
    pass


class Command(BaseCommand):
    help = "Run deamon."

    def handle(self, *_, **__):
        run()
