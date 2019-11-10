from django.db import models


class Globals(models.Model):
    gs_webhook_working = models.BooleanField(default=False)
    gs_webhook_fired = models.BooleanField(default=False)

    @property
    def instance(self) -> "Globals":
        try:
            i = Globals.objects.first()
            assert i.pk
        except:
            i = Globals()
            i.save()

        return i

