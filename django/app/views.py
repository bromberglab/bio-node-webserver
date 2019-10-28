import os
from django.shortcuts import render, redirect
from django.views import View as RegView
from django.http import HttpResponse, Http404
from django.conf import settings
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

# Create your views here.

from .models import *
from .files import handle_uploaded_file, get_upload, file_tree, finish_upload
from .serializers import *


@login_required
def login_index_view(request):
    return Response()


class IndexView(APIView):
    def get(self, request, format=None):
        if request.headers.get('User-Agent', '').startswith('GoogleHC'):
            return Response("ok")
        if settings.DEBUG:
            return Response("Bio Node")

        if not request.user.is_authenticated:
            return login_index_view(request)

        return redirect("/app")


class AdminCreationView(APIView):
    def get(self, request, format=None):
        import random
        import string

        try:
            User.objects.get(username="admin")
            return Response("User exists")

        except User.DoesNotExist:
            a = User(username='admin', email="admin@localhost")
            pw = ''.join(random.choices(
                string.ascii_lowercase + string.digits + '!+-._', k=24))
            a.set_password(pw)
            a.is_superuser = True
            a.is_staff = True
            a.save()
            return Response("admin:" + pw)


class WorkflowStorageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        name = request.GET.get("name", "")
        flow = Workflow.objects.get(name=name)

        return Response(flow.json)

    def post(self, request, format=None):
        name = request.data.get("name", "")
        try:
            flow = Workflow.objects.get(name=name)
        except:
            flow = Workflow(name=name)
        flow.json = request.data.get("data", dict())
        flow.user = request.user
        flow.save()

        return Response()


class ListImagesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        images = NodeImage.objects.all()
        images = [
            {
                'name': i.name,
                'labels': i.labels
            } for i in images
        ]

        return Response(images)


class InspectImageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, name, format=None):
        try:
            image = NodeImage.objects.get(name=name)
        except:
            return Response(status=404)
        tags = image.tag_refs.all()
        tags = [
            {
                'name': i.name,
                'sha': i.sha
            } for i in tags
        ]
        return Response({
            'name': name,
            'labels': image.labels,
            'cmd': image.cmd,
            'env': image.env,
            'tags': tags
        })


class CommitView(APIView):
    def get(self, request, format=None):
        with open(".commit", "r") as f:
            return Response(f.read().replace('\n', ''))


class CronView(APIView):
    def post(self, request, format=None):
        from app.management.commands.cron import cron

        cron()
        return Response('ok')


class GoogleStorageWebhook(APIView):
    def post(self, request):
        if request.headers.get('X-Goog-Channel-Token', '-') == os.environ.get('gs_secret', '-'):
            glob = Globals().instance
            glob.gs_webhook_fired = True
            glob.gs_webhook_working = True
            glob.save()

        return Response("ok")


class FileUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def put(self, request, name=None, format=None):
        handle_uploaded_file(request)

        return Response(status=200)


class CheckAuthView(APIView):
    def get(self, request, format=None):
        return Response(request.user.is_authenticated or settings.DEBUG)


class MyUploadView(viewsets.ViewSet):
    def retrieve(self, request):
        upload = get_upload(request)
        serializer = UploadSerializer(upload)
        return Response(serializer.data)

    def update(self, request):
        upload = get_upload(request)
        serializer = UploadSerializer(upload, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if upload.is_finished:
            finish_upload(request, upload)
        return Response(serializer.data)


class UploadTreeView(APIView):
    def get(self, request, format=None):
        upload = get_upload(request)
        tree = file_tree(upload.file_type, upload.uuid)
        return Response(tree)


class FileTypeListView(ListAPIView):
    queryset = FileType.objects.all()
    serializer_class = FileTypeSerializer
    permission_classes = [IsAuthenticated]
