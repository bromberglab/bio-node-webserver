from django.db import models
import json
import uuid as uu
from django.contrib.auth.models import User
from django.conf import settings
from typing import Union
from app.events import send_event


class CronJob(models.Model):
    name = models.CharField(max_length=32, primary_key=True)
    last_ran = models.DateTimeField()


class NodeImage(models.Model):
    name = models.CharField(max_length=128, primary_key=True)
    labels_string = models.TextField(default="{}")
    cmd_string = models.TextField(default="[]")
    entrypoint_string = models.TextField(default="[]")
    env_string = models.TextField(default="[]")

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
    def entrypoint(self):
        return json.loads(self.entrypoint_string)

    @entrypoint.setter
    def entrypoint(self, entrypoint):
        self.entrypoint_string = json.dumps(entrypoint)

    @property
    def env(self):
        return json.loads(self.env_string)

    @env.setter
    def env(self, env):
        self.env_string = json.dumps(env)

    @property
    def bio_node_entrypoint(self):
        return self.labels.get("bio-node_entrypoint", False)

    @property
    def inputs_raw(self):
        labels = self.labels
        if labels.get("input_1", False):
            # Multi-input mode
            inputs = []
            try:
                i = 1
                while True:
                    inputs.append(labels["input_" + str(i)])
                    i += 1
            except:  # input_k+1 does not exist, throws
                pass
            return inputs
        single_input = labels.get("input", False)
        if single_input:
            # Single-input mode
            return [single_input]
        # No-input mode
        return []

    @property
    def inputs_meta(self):
        inputs = self.inputs_raw

        result = []
        for i in inputs:
            input = i.split(",")
            defaults = ["file", "", "required", "filename", ""]

            if len(input) >= 2 and input[1] == "stdin":
                defaults[3] = "content"

            for i in range(len(defaults)):
                try:
                    assert input[i] != ""
                except:
                    input.append(defaults[i])
            result.append(input)

        return result

    @property
    def inputs(self):
        return [i[0] for i in self.inputs_meta]

    @property
    def outputs_raw(self):
        labels = self.labels
        if labels.get("output_1", False):
            # Multi-output mode
            outputs = []
            try:
                i = 1
                while True:
                    outputs.append(labels["output_" + str(i)])
                    i += 1
            except:  # output_k+1 does not exist, throws
                pass
            return outputs
        single_output = labels.get("output", False)
        if single_output:
            # Single-output mode
            return [single_output]
        # No-output mode
        return []

    @property
    def outputs_meta(self):
        outputs = self.outputs_raw

        result = []
        for i in outputs:
            output = i.split(",")
            defaults = ["file", "stdout", "results.out"]

            if len(output) >= 3 and output[2] == "":
                # If the output filename is '', then don't override it. Foldername will be used as parameter.
                defaults[3] = ""

            for i in range(len(defaults)):
                try:
                    assert output[i] != ""
                except:
                    output.append(defaults[i])
            result.append(output)

        return result

    @property
    def outputs(self):
        return [i[0] for i in self.outputs_meta]


class FileType(models.Model):
    name = models.CharField(max_length=64, primary_key=True)


class Workflow(models.Model):
    name = models.CharField(max_length=64, default=uu.uuid4)
    json_string = models.TextField(default="{}")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    should_run = models.BooleanField(default=False)
    scheduled = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)
    status = models.CharField(max_length=32, blank=True, default="")

    @property
    def json(self):
        return json.loads(self.json_string)

    @json.setter
    def json(self, value):
        self.json_string = json.dumps(value)

    def finish(self):
        self.finished = True
        self.status = "finished"
        self.save()


class NodeImageTag(models.Model):
    image = models.ForeignKey(
        NodeImage, related_name="tag_refs", on_delete=models.CASCADE
    )
    sha = models.CharField(max_length=64)
    name = models.CharField(max_length=64, blank=True, default="")

    def __str__(self):
        return self.name if self.name else self.sha


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

    dependencies = models.ManyToManyField(
        "app.Job", related_name="dependents", blank=True
    )

    @property
    def json(self):
        return json.loads(self.json_string)

    @json.setter
    def json(self, value):
        self.json_string = json.dumps(value)

    def create_json(
        self, image, input_paths, cont_input_paths, output_paths, cont_output_paths
    ):
        import yaml
        import os

        yaml_dir = settings.BASE_DIR
        yaml_dir = os.path.join(yaml_dir, "kube_templates")
        yaml_dir = os.path.join(yaml_dir, "job.yml")

        with open(yaml_dir, "r") as f:
            body = yaml.safe_load(f)

        c = body["spec"]["template"]["spec"]["containers"][0]

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

        c["volumeMounts"] = mounts

        env = image["env"]
        c["env"] = []
        for e in env:
            c["env"].append(
                {"name": e.split("=")[0], "value": "=".join(e.split("=")[1:])}
            )

        bio_node_entrypoint = image["bio_node_entrypoint"]
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

        ignore_entrypoint = image["labels"].get("ignore_entrypoint", False)
        if not ignore_entrypoint:
            c["env"].append({"name": "PREV_ENTRYPOINT", "value": entrypoint})

        ignore_cmd = image["labels"].get("ignore_cmd", True)
        if not ignore_cmd:
            c["env"].append({"name": "PREV_COMMAND", "value": cmd})

        param = image["labels"].get("parameters", "")
        c["env"].append({"name": "ADD_PARAMETERS", "value": param})

        c["env"].append({"name": "INPUTS_META", "value": inputs})
        c["env"].append({"name": "OUTPUTS_META", "value": outputs})

        return body

    def create_body(self):
        if self.body:
            return

        conf = self.json

        id = conf["id"]

        image = conf["data"]["image"]

        out_path = "data/job_outputs/" + id

        i = 0
        input_paths = []
        cont_input_paths = []
        for i, inp in enumerate(conf["inputs"].items()):
            inp = inp[1]  # ignore key, take value
            if len(inp["connections"]) == 0:
                continue
            connection = inp["connections"][0]  # TODO: multiple?
            cont_input_paths.append("/input/" + str(i + 1))
            inp_id = connection["node"]  # TODO: multiple
            inp_job = Job.objects.get(pk=inp_id)
            inp_path = "data/job_outputs/" + inp_id
            if inp_job.is_data_input:
                inp_path = (
                    "data/" + inp_job.data_input_type + "/" + str(inp_job.data_id)
                )
            elif not inp_job.is_single_output:
                inp_path += "/" + connection.output[2:]
            input_paths.append(inp_path)
        if len(cont_input_paths) == 1:
            cont_input_paths = ["/input"]

        if self.is_single_output:
            output_paths = [out_path]
            cont_output_paths = ["/output"]
        else:
            output_paths = []
            cont_output_paths = []
            for i in range(len(conf["outputs"])):
                output_paths.append(out_path + "/" + str(i + 1))
                cont_output_paths.append("/output/" + str(i + 1))

        self.body = json.dumps(
            self.create_json(
                image, input_paths, cont_input_paths, output_paths, cont_output_paths
            )
        )

    @property
    def is_node(self):
        return self.json["data"]["id"].startswith("node/")

    @property
    def is_data_input(self):
        return self.json["data"]["id"].startswith("from_data/")

    @property
    def is_data_output(self):
        return self.json["data"]["id"].startswith("to_data/")

    @property
    def data_input_type(self):
        return self.json["name"][len("from_data/") :]

    @property
    def data_type(self):
        if self.is_data_input:
            return self.data_input_type

        return self.data_output_type

    @property
    def data_output_type(self):
        return self.json["name"][len("to_data/") :]

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

    def finish(self):
        self.finished = True
        self.save()

        self.status_change()

    def status_change(self):
        from app.serializers import JobSerializer

        data = JobSerializer(self).data
        data["type"] = "job"
        send_event("status-change", data)


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


class Download(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    path = models.TextField(default="")
