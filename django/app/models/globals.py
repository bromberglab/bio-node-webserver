from django.db import models


class Globals(models.Model):
    gs_webhook_working = models.BooleanField(default=False)
    gs_webhook_fired = models.BooleanField(default=False)
    log_chars_kept = models.IntegerField(default=1000)

    @property
    def instance(self) -> "Globals":
        try:
            i = Globals.objects.first()
            assert i.pk
        except:
            i = Globals()
            i.save()

        return i

