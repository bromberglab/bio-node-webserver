from rest_framework import serializers

from .models import *


class UploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Upload
        fields = ['uuid', 'file_type', 'job_count',
                  'is_finished', 'name', 'display_name']
        read_only_fields = ['uuid', 'display_name', 'is_finished']


class FileTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileType
        fields = ['name']
        read_only_fields = ['name']


class NodeImageTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = NodeImageTag
        read_only_fields = fields = [
            'name', 'sha']


class NodeImageSerializer(serializers.ModelSerializer):
    tags = NodeImageTagSerializer(many=True)

    class Meta:
        model = NodeImage
        read_only_fields = fields = [
            'name', 'labels', 'cmd', 'env', 'inputs', 'outputs', 'tags']


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        read_only_fields = fields = ['uuid', 'scheduled', 'finished',
                                     'status', 'dependencies_met', 'old_id']
