from django.db import models
from django.contrib.auth.models import User
import json
import re


class FileType(models.Model):
    name = models.CharField(max_length=64, primary_key=True)


def update_dict(base, changes):
    for k, v in changes.items():
        base[k] = v
        if v is None:
            del base[k]

    return base


class NodeImage(models.Model):
    name = models.CharField(max_length=128, primary_key=True)
    labels_string = models.TextField(default="{}")
    cmd_string = models.TextField(default="[]")
    entrypoint_string = models.TextField(default="[]")
    env_string = models.TextField(default="{}")
    override_string = models.TextField(default="{}")

    imported = models.BooleanField(default=False)
    imported_tag = models.CharField(max_length=128, default="", blank=True)
    imported_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True
    )
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def tags(self):
        return self.tag_refs

    @property
    def override(self):
        return json.loads(self.override_string)

    @override.setter
    def override(self, override):
        labels = self.labels
        items = list(override.get("labels", {}).items())
        for k, v in items:
            try:
                assert labels[k] == v
                del override["labels"][k]
            except:
                pass
        env = self.env
        items = list(override.get("env", {}).items())
        for k, v in items:
            try:
                assert env[k] == v
                del override["env"][k]
            except:
                pass

        try:
            assert env["cmd"] == self.cmd
            del override["cmd"]
        except:
            pass
        try:
            assert env["entrypoint"] == self.entrypoint
            del override["entrypoint"]
        except:
            pass

        self.override_string = json.dumps(override)

    @property
    def labels(self):
        override = json.loads(self.override_string)
        if override.get("labels", None) is not None:
            return update_dict(json.loads(self.labels_string), override["labels"])

        return json.loads(self.labels_string)

    @labels.setter
    def labels(self, labels):
        self.labels_string = json.dumps(labels)

    @property
    def cmd(self):
        override = json.loads(self.override_string)
        if override.get("cmd", None) is not None:
            return override["cmd"]

        return json.loads(self.cmd_string)

    @cmd.setter
    def cmd(self, cmd):
        self.cmd_string = json.dumps(cmd)

    @property
    def entrypoint(self):
        override = json.loads(self.override_string)
        if override.get("entrypoint", None) is not None:
            return override["entrypoint"]

        return json.loads(self.entrypoint_string)

    @entrypoint.setter
    def entrypoint(self, entrypoint):
        self.entrypoint_string = json.dumps(entrypoint)

    @property
    def env(self):
        override = json.loads(self.override_string)
        if override.get("env", None) is not None:
            return update_dict(json.loads(self.env_string), override["env"])

        return json.loads(self.env_string)

    @env.setter
    def env(self, env):
        self.env_string = json.dumps(env)

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
            i = re.sub(r",\s+", ",", i)
            input = i.split(",")
            defaults = ["file", "", "required", "filename", "*"]

            if len(input) >= 2 and input[1] == "stdin":
                defaults[3] = "content"
            if len(input) > 4:
                defaults[4] = input[4]

            for i in range(len(defaults)):
                try:
                    assert input[i] != ""
                except:
                    if len(input) > i:
                        input[i] = defaults[i]
                    else:
                        input.append(defaults[i])
            result.append(input)

        return result

    @property
    def inputs(self):
        inputs = [i[0] for i in self.inputs_meta]
        p = "consumable "
        inputs = [i[len(p) :] if i.startswith(p) else i for i in inputs]

        return inputs

    @property
    def add_input(self):
        labels = self.labels
        inp = labels.get("input_n", False)
        if not inp:
            return False
        return re.sub(r",\s+", ",", inp).split(",")[0]

    @property
    def add_output(self):
        labels = self.labels
        out = labels.get("output_n", False)
        if not out:
            return False
        return re.sub(r",\s+", ",", out).split(",")[0]

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
            i = re.sub(r",\s+", ",", i)
            output = i.split(",")
            defaults = ["file", "stdout", "results.out"]

            if len(output) >= 3 and output[2] == "":
                # If the output filename is '', then don't override it. Foldername will be used as parameter.
                defaults[2] = ""
            if len(output) >= 2 and output[1] == "workingdir":
                # Default for workingdir: Move all created files
                defaults[2] = ""

            for i in range(len(defaults)):
                try:
                    assert output[i] != ""
                except:
                    if len(output) > i:
                        output[i] = defaults[i]
                    else:
                        output.append(defaults[i])
            result.append(output)

        return result

    @property
    def outputs(self):
        return [i[0] for i in self.outputs_meta]


class NodeImageTag(models.Model):
    image = models.ForeignKey(
        NodeImage, related_name="tag_refs", on_delete=models.CASCADE
    )
    sha = models.CharField(max_length=64)
    name = models.CharField(max_length=64, blank=True, default="")

    def __str__(self):
        return self.name if self.name else self.sha
