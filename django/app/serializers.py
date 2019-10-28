from rest_framework import serializers

from .models import *


class UploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Upload
        fields = ['uuid', 'file_type', 'job_count', 'is_finished']
        read_only_fields = ['uuid']


class FileTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileType
        fields = ['name']
        read_only_fields = ['name']
