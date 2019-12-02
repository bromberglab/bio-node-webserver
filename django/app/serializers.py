from rest_framework import serializers

from .models import *


class UploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Upload
        fields = [
            "uuid",
            "file_type",
            "job_count",
            "is_finished",
            "name",
            "display_name",
        ]
        read_only_fields = ["uuid", "display_name", "is_finished"]


class FileTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileType
        fields = ["name"]
        read_only_fields = ["name"]


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
            "outputs",
            "outputs_meta",
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
            "old_id",
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
            "name",
            "user",
            "should_run",
            "scheduled",
            "finished",
            "status",
            "some_failed",
        ]
