import uuid as uu
from django.db import models
from django.contrib.auth.models import User
from typing import Union


class Upload(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uu.uuid4, editable=False)
    name = models.CharField(max_length=64, blank=True, default="")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    file_type = models.CharField(max_length=64, default="file")
    started_at = models.DateTimeField(auto_now_add=True)
    is_finished = models.BooleanField(default=False)
    is_newest = models.BooleanField(default=True)
    job_count = models.CharField(
        choices=(("auto", "Auto"), ("single", "Single"), ("multiple", "Multiple"),),
        max_length=16,
        default="auto",
    )

    @property
    def display_name(self):
        if self.name:
            return self.name
        return str(self.uuid)

    @classmethod
    def for_name(cls, name, type="file") -> Union["Upload", None]:
        return cls.objects.filter(name=name, is_newest=True, file_type=type).first()

    def make_download_link(self):
        from app.files import make_download_link

        path = self.file_type + "/" + str(self.uuid)
        return make_download_link(
            rel_path=path, name=self.name if self.name else "download"
        )

    def __str__(self):
        return self.name if self.name else str(self.uuid)

    def save(self, *args, **kwargs):
        if self.is_finished and self.is_newest:
            for u in Upload.objects.filter(
                name=self.name, is_newest=True, file_type=self.file_type
            ).exclude(pk=self.pk):
                u.is_newest = False
                u.save()

        return super().save(*args, **kwargs)
