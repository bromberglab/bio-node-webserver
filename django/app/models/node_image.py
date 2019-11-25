from django.db import models
from django.contrib.auth.models import User
import json


class FileType(models.Model):
    name = models.CharField(max_length=64, primary_key=True)


class NodeImage(models.Model):
    name = models.CharField(max_length=128, primary_key=True)
    labels_string = models.TextField(default="{}")
    cmd_string = models.TextField(default="[]")
    entrypoint_string = models.TextField(default="[]")
    env_string = models.TextField(default="[]")

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
                defaults[2] = ""
            if len(output) >= 2 and output[1] == "workingdir":
                # Default for workingdir: Move all created files
                defaults[2] = ""

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


class NodeImageTag(models.Model):
    image = models.ForeignKey(
        NodeImage, related_name="tag_refs", on_delete=models.CASCADE
    )
    sha = models.CharField(max_length=64)
    name = models.CharField(max_length=64, blank=True, default="")

    def __str__(self):
        return self.name if self.name else self.sha
