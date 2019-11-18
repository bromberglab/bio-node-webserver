from django.db import models
import uuid as uu


class Globals(models.Model):
    some_uuid = models.UUIDField(default=uu.uuid4)
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

    @property
    def random(self):
        r = str(self.some_uuid)
        r = r.split("-")[0]

        return r
