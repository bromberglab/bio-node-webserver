from django.db import models
import json
import uuid as uu
from django.contrib.auth.models import User
import time
import random
import string
from app.events import send_event


class Workflow(models.Model):
    name = models.CharField(max_length=64, default=uu.uuid4)
    json_string = models.TextField(default="{}")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    should_run = models.BooleanField(default=False)
    scheduled = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)
    status = models.CharField(max_length=32, blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def json(self):
        return json.loads(self.json_string)

    @json.setter
    def json(self, value):
        self.json_string = json.dumps(value)

    def finish(self):
        self.finished = True
        self.status = "finished"
        send_event("workflow-finished", {"pk": self.pk})

        self.save()
        self.clean_up()

    def clean_up(self):
        for job in self.job_set.all():
            job.clean_up()

    @classmethod
    def id_for(cls, key, workflow_ids):
        key = str(key)
        workflow_ids[key] = workflow_ids.get(key, str(uu.uuid4()))
        return workflow_ids[key]

    def prepare_workflow(self):
        body = self.json

        nodes = {}
        workflow_ids = {}

        for key, value in body["nodes"].items():
            i = Workflow.id_for(key, workflow_ids)
            value["id"] = i
            value["old_id"] = key
            for _, v in value["inputs"].items():
                v = v["connections"]
                for c in v:
                    c["node"] = Workflow.id_for(c["node"], workflow_ids)
            for _, v in value["outputs"].items():
                v = v["connections"]
                for c in v:
                    c["node"] = Workflow.id_for(c["node"], workflow_ids)
            nodes[i] = value
        body["nodes"] = nodes
        self.json = body
        self.save()

    def launch_workflow(self):
        from .job import Job

        body = self.json

        jobs = []
        for i, node in body["nodes"].items():
            j = Job(uuid=i, workflow=self, dependencies_met=False)
            j.json = node
            j.save()
            jobs.append(j)

            # temporary property
            j.has_no_dependencies = True

        for j in jobs:
            node = body["nodes"][j.pk]
            for _, inp in node["inputs"].items():
                for c in inp["connections"]:
                    dep = Job.objects.get(pk=c["node"])
                    j.dependencies.add(dep)
                    j.has_no_dependencies = False
            j.save()

        for j in filter(lambda j: j.has_no_dependencies, jobs):
            j.dependencies_met = True
            j.save()

    def run_workflow(self):
        rnd = "".join(random.choices(string.ascii_lowercase + string.digits, k=5))

        self.status = rnd
        self.scheduled = True
        self.save()

        # break race condition:
        time.sleep(0.1)
        self = Workflow.objects.get(pk=self.pk)
        if self.status != rnd:
            return

        self.launch_workflow()
        self.status = "running"

        self.save()

    @property
    def some_failed(self):
        from .job import Job

        if not self.should_run:
            return False
        if not self.finished:
            return False

        nodes = self.json["nodes"]
        for k, v in nodes.items():
            job = Job.objects.get(uuid=k)
            if job.is_node and job.status != "succeeded":
                return True
        return False
