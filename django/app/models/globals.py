from django.db import models
import uuid as uu
import json


class Globals(models.Model):
    class Meta:
        permissions = [
            ("is_guest_user", "This user has the status Guest."),
        ]

    some_uuid = models.UUIDField(default=uu.uuid4)
    gs_webhook_working = models.BooleanField(default=False)
    gs_webhook_fired = models.BooleanField(default=False)
    log_chars_kept = models.IntegerField(default=1000)
    should_expand = models.BooleanField(default=False)
    drained = models.BooleanField(default=False)
    nodes_string = models.TextField(default="[]")

    @property
    def nodes(self):
        return json.loads(self.nodes_string)

    @nodes.setter
    def nodes(self, value):
        self.nodes_string = json.dumps(value)

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
