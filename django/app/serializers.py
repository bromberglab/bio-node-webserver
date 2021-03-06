from rest_framework import serializers

from .models import *


class UploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Upload
        fields = [
            "uuid",
            "file_type",
            "started_at",
            "is_newest",
            "is_finished",
            "name",
            "display_name",
            "reassembling",
            "extracting",
            "size",
        ]
        read_only_fields = [
            "uuid",
            "started_at",
            "is_newest",
            "is_finished",
            "display_name",
            "reassembling",
            "extracting",
            "size",
        ]


class FileTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileType
        fields = ["name"]
        read_only_fields = ["name"]


class ApiWorkflowSerializer(serializers.ModelSerializer):

    user = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="username"
    )

    class Meta:
        model = ApiWorkflow
        read_only_fields = fields = ["uuid", "user", "created_at", "run_at"]


class NodeImageTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = NodeImageTag
        read_only_fields = fields = ["name", "sha"]


class NodeImageSerializer(serializers.ModelSerializer):
    tags = NodeImageTagSerializer(many=True)

    class Meta:
        model = NodeImage
        read_only_fields = fields = [
            "name",
            "labels",
            "entrypoint",
            "cmd",
            "env",
            "inputs",
            "inputs_meta",
            "add_input",
            "add_input_meta",
            "outputs",
            "outputs_meta",
            "add_output",
            "add_output_meta",
            "tags",
            "added_at",
            "updated_at",
            "imported_tag",
        ]


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        read_only_fields = fields = [
            "uuid",
            "scheduled",
            "finished",
            "status",
            "dependencies_met",
            "started_at",
            "parallel_runs",
            "finished_runs",
            "finished_at",
            "runtime",
            "max_cpu",
            "max_memory",
            "resource_exhaustion",
        ]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "pk",
            "user",
            "short_text",
            "long_text",
            "importance",
            "created_at",
        ]
        read_only_fields = [
            "pk",
            "user",
            "created_at",
        ]


class WorkflowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflow
        read_only_fields = fields = [
            "pk",
            "name",
            "user",
            "should_run",
            "scheduled",
            "finished",
            "status",
            "some_failed",
            "created_at",
            "updated_resources",
        ]
