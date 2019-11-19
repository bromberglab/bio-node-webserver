from django.db import models
import json
import uuid as uu
from django.conf import settings
from app.events import send_event
import time
import random
import string
from kubernetes import client, watch
from django.db import transaction
from ..files import copy_folder, list_dirs
from .workflow import Workflow
from .upload import Upload
from .node_image import NodeImage
from .globals import Globals
from .notification import Notification
from ..kube import get_status as kube_status
from pathlib import Path


class Job(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uu.uuid4, editable=False)
    scheduled = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)
    body = models.TextField(blank=True, default="")
    json_string = models.TextField(default="{}")
    status = models.CharField(max_length=32, blank=True, default="")
    dependencies_met = models.BooleanField(default=True)
    workflow = models.ForeignKey(
        Workflow, null=True, blank=True, on_delete=models.SET_NULL
    )
    parallel_runs = models.IntegerField(default=-1)

    dependencies = models.ManyToManyField(
        "app.Job", related_name="dependents", blank=True
    )

    @property
    def json(self):
        return json.loads(self.json_string)

    @json.setter
    def json(self, value):
        self.json_string = json.dumps(value)

    def create_body(
        self, image, input_paths, cont_input_paths, output_paths, cont_output_paths, k
    ):
        import yaml
        import os

        yaml_dir = settings.BASE_DIR
        yaml_dir = os.path.join(yaml_dir, "kube_templates")
        yaml_dir = os.path.join(yaml_dir, "job.yml")

        with open(yaml_dir, "r") as f:
            body = yaml.safe_load(f)

        c = body["spec"]["template"]["spec"]["containers"][0]
        resources = c["resources"]["requests"]
        resources["memory"] = image["labels"].get("memory", resources["memory"])
        resources["cpu"] = image["labels"].get("cpu", resources["cpu"])

        tag = image["name"]
        img: NodeImage = NodeImage.objects.get(name=tag)
        c["image"] = tag

        mounts = []
        for i, host_path in enumerate(input_paths):
            cont_path = cont_input_paths[i]
            mounts.append(
                {
                    "name": "vol",
                    "mountPath": cont_path,
                    "subPath": host_path,
                    "readOnly": True,
                }
            )
        for i, host_path in enumerate(output_paths):
            cont_path = cont_output_paths[i]
            mounts.append({"name": "vol", "mountPath": cont_path, "subPath": host_path})
        mounts.append({"name": "vol", "mountPath": "/bio-node", "subPath": "bio-node"})

        c["volumeMounts"] = mounts

        env = image["env"]
        c["env"] = []
        for e in env:
            c["env"].append(
                {"name": e.split("=")[0], "value": "=".join(e.split("=")[1:])}
            )

        bio_node_entrypoint = image.get("bio-node_entrypoint", "/bio-node/entry.sh")
        if bio_node_entrypoint:
            c["command"] = bio_node_entrypoint.split(" ")
            c["args"] = []

        else:
            if len(image["entrypoint"]):
                c["command"] = image["entrypoint"]
                c["args"] = image["cmd"]
            else:
                c["command"] = image["cmd"]
                c["args"] = []

        entrypoint = " ".join(image["entrypoint"])
        cmd = " ".join(image["cmd"])
        inputs = ";".join([",".join(i) for i in image["inputs_meta"]])
        outputs = ";".join([",".join(i) for i in image["outputs_meta"]])

        app_entrypoint = image["labels"].get("app_entrypoint", None)
        if app_entrypoint is None:
            c["env"].append({"name": "PREV_ENTRYPOINT", "value": entrypoint})
        else:
            c["env"].append({"name": "PREV_ENTRYPOINT", "value": app_entrypoint})

        ignore_cmd = image["labels"].get("ignore_cmd", True)
        if ignore_cmd in [0, "0", False, "false", "no", "f", "n"]:
            c["env"].append({"name": "PREV_COMMAND", "value": cmd})

        timeout = image["labels"].get("timeout", None)
        if timeout is not None:
            c["env"].append({"name": "TIMEOUT", "value": str(timeout)})

        param = image["labels"].get("parameters", "")
        c["env"].append({"name": "ADD_PARAMETERS", "value": param})

        c["env"].append({"name": "INPUTS_META", "value": inputs})
        c["env"].append({"name": "OUTPUTS_META", "value": outputs})
        c["env"].append({"name": "K", "value": str(k)})
        c["env"].append({"name": "I", "value": "0"})

        return body

    def find_inputs(self):
        conf = self.json
        input_paths = []
        cont_input_paths = []
        for i, inp in enumerate(conf["inputs"].items()):
            inp = inp[1]  # ignore key, take value
            if len(inp["connections"]) == 0:
                continue
            # There should only be 1 input connection.
            connection = inp["connections"][0]
            cont_input_paths.append("/input/" + str(i + 1))
            inp_id = connection["node"]
            inp_job = Job.objects.get(pk=inp_id)
            inp_path = "data/job_outputs/" + inp_id
            if inp_job.is_data_input:
                inp_path = (
                    "data/" + inp_job.data_input_type + "/" + str(inp_job.data_id)
                )
            elif not inp_job.is_single_output:
                inp_path += "/" + connection["output"][2:]
            input_paths.append(inp_path)
        if len(conf["inputs"].items()) == 1:
            cont_input_paths = ["/input"]

        return input_paths, cont_input_paths

    def prepare_job(self):
        if self.body:
            return

        conf = self.json

        id = conf["id"]

        image = conf["data"]["image"]

        parallelism = image["labels"].get("parallelism", "1.0")
        parallelism = float(parallelism)
        assert 0.0 <= parallelism <= 1.0

        out_path = "data/job_outputs/" + id

        i = 0
        input_paths, cont_input_paths = self.find_inputs()

        if self.is_single_output:
            output_paths = [out_path]
            cont_output_paths = ["/output"]
        else:
            output_paths = []
            cont_output_paths = []
            for i in range(len(conf["outputs"])):
                output_paths.append(out_path + "/" + str(i + 1))
                cont_output_paths.append("/output/" + str(i + 1))

        if parallelism > 0:
            if len(input_paths) == 1:
                path = input_paths[0]
            else:
                inputs = image["inputs_meta"]
                path = None
                for t in ["required", "optional", "static"]:
                    for i in range(len(inputs)):
                        if path is not None:
                            break
                        if inputs[i][2] == t:
                            for j in range(len(input_paths)):
                                if cont_input_paths[j].endswith("/" + str(i + 1)):
                                    path = input_paths[j]
                                    break

            if path is None:
                k = -1
                u = self.workflow.user
                n = conf["displayName"]
                Notification.send(
                    u,
                    "Warning: No parallelism for %s" % n,
                    "Your job is not running in parallel. This might be caused by a job without inputs.",
                    10,
                )
            else:
                path = Path(settings.DATA_PATH) / path
                jobs = list_dirs(path)

                n = len(jobs)
                k = n * parallelism
                k = int(k)
                if k < 1:
                    k = 1
                self.parallel_runs = k
                self.save()
                k = int((n // (k + 0.0001)) + 1)
        else:
            k = -1

        self.body = json.dumps(
            self.create_body(
                image, input_paths, cont_input_paths, output_paths, cont_output_paths, k
            )
        )

    @property
    def is_node(self):
        return self.json["name"].startswith("node/")

    @property
    def is_data_input(self):
        return self.json["name"].startswith("from_data")

    @property
    def is_data_output(self):
        return self.json["name"].startswith("to_data")

    @property
    def data_input_type(self):
        return self.json["data"]["type"]

    @property
    def data_type(self):
        if self.is_data_input:
            return self.data_input_type

        return self.data_output_type

    @property
    def data_output_type(self):
        return self.json["data"]["type"]

    @property
    def data_name(self):
        return self.json["data"]["data_name"]

    @property
    def data_id(self):
        data_name = self.data_name
        upload = Upload.for_name(data_name, self.data_type)

        if not upload:
            upload = Upload(file_type=self.data_type, is_finished=True, name=data_name)
            upload.save()
        return upload.uuid

    @property
    def old_id(self):
        return self.json["old_id"]

    @property
    def is_single_input(self):
        if not self.is_node:
            return True
        return len(self.json["inputs"]) <= 1

    @property
    def is_single_output(self):
        if not self.is_node:
            return True
        return len(self.json["outputs"]) <= 1

    @property
    def display_name(self):
        return self.json["data"]["displayName"]

    def finish(self):
        self.finished = True
        self.save()

        self.status_change()

    def status_change(self):
        from app.serializers import JobSerializer

        data = JobSerializer(self).data
        data["type"] = "job"
        send_event("status-change", data)

    def get_status(self):
        status = None
        logs = ""
        if self.parallel_runs < 0:
            status, pod, logs = kube_status(str(self.pk))
        else:
            k8s_v1 = client.CoreV1Api()
            k8s_batch_v1 = client.BatchV1Api()
            for i in range(self.parallel_runs):
                name = str(self.pk) + "-" + str(i)
                job_status, pod, job_logs = kube_status(name)
                if status is None or job_status == "failed":
                    status = job_status
                    logs += job_logs

                resp = k8s_batch_v1.delete_namespaced_job(name, namespace="default")
                resp = k8s_v1.delete_namespaced_pod(str(pod), namespace="default")
        length = Globals().instance.log_chars_kept

        if len(logs) > length:
            length = length // 2 - 5
            logs = logs[:length] + "\n...\n" + logs[-length:]

        Notification.job_finished(self, status, pod, logs)

        return status, pod

    def create_output(self):
        conf = self.json
        data_output_type = self.data_output_type
        data_id = str(self.data_id)
        out_path = "data/" + data_output_type + "/" + data_id

        input_paths, cont_input_paths = self.find_inputs()

        if len(input_paths) != 1:
            return  # misconfigured, ignore.

        copy_folder(input_paths[0], out_path)

    def launch_job(self):
        dep = json.loads(self.body)

        k8s_batch_v1 = client.BatchV1Api()
        if self.parallel_runs < 0:
            dep["metadata"]["name"] = str(self.pk)
            resp = k8s_batch_v1.create_namespaced_job(body=dep, namespace="default")
        for i in range(self.parallel_runs):
            dep["metadata"]["name"] = str(self.pk) + "-" + str(i)
            c = dep["spec"]["template"]["spec"]["containers"][0]
            c["env"][-1]["value"] = str(i)
            resp = k8s_batch_v1.create_namespaced_job(body=dep, namespace="default")

    def delete_job(self, pod):
        k8s_batch_v1 = client.BatchV1Api()
        k8s_v1 = client.CoreV1Api()
        resp = k8s_batch_v1.delete_namespaced_job(str(self.pk), namespace="default")
        resp = k8s_v1.delete_namespaced_pod(str(pod), namespace="default")

    def run_job(self):
        try:
            self.run_job_()
        except Exception as e:
            import traceback

            if self.workflow and self.workflow.user:
                u = self.workflow.user
                e = str(e) + "\n" + traceback.format_exc()
                Notification.send(u, "Scheduling Failed", e, 15)
            else:
                raise e

    def run_job_(self):
        rnd = "".join(random.choices(string.ascii_lowercase + string.digits, k=5))

        self.status = rnd
        self.scheduled = True
        self.save()

        # break race condition:
        time.sleep(0.1)
        job = Job.objects.get(pk=self.pk)
        if job.status != rnd:
            return

        job.status_change()
        status = ""
        if job.is_node:
            job.prepare_job()
            job.launch_job()
            status, pod = job.get_status()

            if job.parallel_runs < 0:
                job.delete_job(pod)
        elif job.is_data_output:
            job.create_output()

        job.status = status

        with transaction.atomic():
            job.finish()

            w = job.workflow
            if w and w.job_set.filter(finished=False).count() == 0:
                w.finish()

        job = Job.objects.get(pk=job.pk)
        for dependent in job.dependents.all():
            with transaction.atomic():
                dependent.dependencies.remove(job)
                if dependent.dependencies.count() == 0:
                    dependent.dependencies_met = True
                dependent.save()
