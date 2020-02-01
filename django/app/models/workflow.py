from django.db import models
import json
import uuid as uu
from django.contrib.auth.models import User
import time
import random
import string
from app.events import send_event
from app.util import default_name


class ApiWorkflow(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uu.uuid4, editable=False)
    json_string = models.TextField(default="{}")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    outputs_count = models.IntegerField(default=-1)

    @property
    def json(self):
        return json.loads(self.json_string)

    @json.setter
    def json(self, value):
        self.json_string = json.dumps(value)

    def prepare(self):
        uuid = str(self.uuid)
        body = self.json

        inputs = {}
        outputs = {}

        for id, node in body["nodes"].items():
            name = node["name"]
            if name.startswith("from_data"):
                n = "i/%d" % (len(inputs) + 1)

                inputs[n] = "[%s]/[%s]" % (
                    node["data"]["type"],
                    node["data"]["data_name"],
                )

                node["data"]["type"] = uuid
                node["data"]["data_name"] = n
            if name.startswith("to_data"):
                n = "o/%d" % (len(outputs) + 1)

                outputs[n] = "[%s]/[%s]" % (
                    node["data"]["type"],
                    node["data"]["data_name"],
                )

                node["data"]["type"] = uuid
                node["data"]["data_name"] = n
        self.json = body
        self.outputs_count = len(outputs)

        return inputs, outputs


class Workflow(models.Model):
    name = models.CharField(max_length=64, default=default_name)
    json_string = models.TextField(default="{}")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    should_run = models.BooleanField(default=False)
    scheduled = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)
    status = models.CharField(max_length=32, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    is_shared = models.BooleanField(default=False)
    updated_resources = models.BooleanField(default=False)
    api_workflow = models.ForeignKey(
        ApiWorkflow, null=True, blank=True, on_delete=models.SET_NULL
    )

    def update_resources(self):
        from app.models import Job

        if not self.finished:
            return False
        if self.some_failed:
            return False
        if self.updated_resources:
            return False
        body = self.json
        for i, node in body["nodes"].items():
            try:
                job = Job.objects.get(uuid=i)
            except:
                continue

            cpu = job.max_cpu
            memory = job.max_memory
            if cpu <= 0:
                continue
            if memory <= 0:
                continue
            node["data"]["image"]["labels"]["cpu"] = "%dm" % int(cpu)
            node["data"]["image"]["labels"]["memory"] = "%dMi" % int(memory)
        self.json = body
        self.updated_resources = True
        self.save()
        return True

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
        from .upload import Upload
        from app.files import clear_upload

        for job in self.job_set.all():
            job.clean_up()
        if self.api_workflow is not None:
            pk = str(self.api_workflow.pk)
            for u in Upload.objects.filter(file_type=pk):
                if u.name.startswith("i/"):
                    clear_upload(u)
                    u.delete()

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
