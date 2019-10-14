from django.db import models
import json


class CronJob(models.Model):
    name = models.CharField(max_length=32, primary_key=True)
    last_ran = models.DateTimeField()


class NodeImage(models.Model):
    name = models.CharField(max_length=128, primary_key=True)
    labels_string = models.TextField()

    @property
    def labels(self):
        return json.loads(self.labels_string)

    @labels.setter
    def labels(self, labels):
        self.labels_string = json.dumps(labels)


class NodeImageTag(models.Model):
    image = models.ForeignKey(
        NodeImage, related_name='tag_refs', on_delete=models.CASCADE)
    sha = models.CharField(max_length=64)
    name = models.CharField(max_length=64, blank=True, default='')
