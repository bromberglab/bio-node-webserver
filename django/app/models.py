from django.db import models
import json
import uuid as uu
from django.contrib.auth.models import User


class CronJob(models.Model):
    name = models.CharField(max_length=32, primary_key=True)
    last_ran = models.DateTimeField()


class NodeImage(models.Model):
    name = models.CharField(max_length=128, primary_key=True)
    labels_string = models.TextField(default='{}')
    cmd_string = models.TextField(default='[]')
    env_string = models.TextField(default='[]')

    @property
    def tags(self):
        return self.tag_refs

    @property
    def labels(self):
        return json.loads(self.labels_string)

    @labels.setter
    def labels(self, labels):
        self.labels_string = json.dumps(labels)

    @property
    def cmd(self):
        return json.loads(self.cmd_string)

    @cmd.setter
    def cmd(self, cmd):
        self.cmd_string = json.dumps(cmd)

    @property
    def env(self):
        return json.loads(self.env_string)

    @env.setter
    def env(self, env):
        self.env_string = json.dumps(env)

    @property
    def inputs(self):
        labels = self.labels
        if labels.get('input_1', False):
            # Multi-input mode
            inputs = []
            try:
                i = 1
                while True:
                    inputs.append(labels['input_' + str(i)])
                    i += 1
            except:  # input_k+1 does not exist, throws
                pass
            return inputs
        single_input = labels.get('input', False)
        if single_input:
            # Single-input mode
            return [single_input]
        # No-input mode
        return []

    @property
    def outputs(self):
        labels = self.labels
        if labels.get('output_1', False):
            # Multi-output mode
            outputs = []
            try:
                i = 1
                while True:
                    outputs.append(labels['output_' + str(i)])
                    i += 1
            except:  # output_k+1 does not exist, throws
                pass
            return outputs
        single_output = labels.get('output', False)
        if single_output:
            # Single-output mode
            return [single_output]
        # No-output mode
        return []


class FileType(models.Model):
    name = models.CharField(max_length=64, primary_key=True)


class Workflow(models.Model):
    name = models.CharField(max_length=64, default=uu.uuid4)
    json_string = models.TextField(default='{}')
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True)
    should_run = models.BooleanField(default=False)
    scheduled = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)
    status = models.CharField(max_length=32, blank=True, default='')

    @property
    def json(self):
        return json.loads(self.json_string)

    @json.setter
    def json(self, value):
        self.json_string = json.dumps(value)


class NodeImageTag(models.Model):
    image = models.ForeignKey(
        NodeImage, related_name='tag_refs', on_delete=models.CASCADE)
    sha = models.CharField(max_length=64)
    name = models.CharField(max_length=64, blank=True, default='')

    def __str__(self):
        return self.name if self.name else self.sha


class Globals(models.Model):
    gs_webhook_working = models.BooleanField(default=False)
    gs_webhook_fired = models.BooleanField(default=False)

    @property
    def instance(self) -> 'Globals':
        try:
            i = Globals.objects.first()
            assert i.pk
        except:
            i = Globals()
            i.save()

        return i


class Job(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uu.uuid4, editable=False)
    scheduled = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)
    body = models.TextField(blank=True, default='')
    json_string = models.TextField(default='{}')
    status = models.CharField(max_length=32, blank=True, default='')
    dependencies_met = models.BooleanField(default=True)
    workflow = models.ForeignKey(
        Workflow, null=True, blank=True, on_delete=models.SET_NULL)

    dependencies = models.ManyToManyField('app.Job', related_name='dependents')

    @property
    def json(self):
        return json.loads(self.json_string)

    @json.setter
    def json(self, value):
        self.json_string = json.dumps(value)

    def create_body(self):
        if self.body:
            return

        # TODO


class Upload(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uu.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True)
    file_type = models.CharField(max_length=64, default='file')
    started_at = models.DateTimeField(auto_now_add=True)
    is_finished = models.BooleanField(default=False)
    job_count = models.CharField(choices=(
        ('auto', "Auto"),
        ('single', "Single"),
        ('multiple', "Multiple"),
    ), max_length=16, default='auto')
