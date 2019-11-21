import os
from django.shortcuts import render, redirect
from django.views import View as RegView
from django.http import HttpResponse, Http404
from django.conf import settings
from django.urls import reverse
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django_zip_stream.responses import FolderZipResponse

# Create your views here.

from .models import *
from .files import (
    handle_uploaded_file,
    get_upload,
    file_tree,
    finish_upload,
    finalize_upload,
)
from .serializers import *


@login_required
def login_index_view(request):
    return Response()


class IndexView(APIView):
    def get(self, request, format=None):
        if request.headers.get("User-Agent", "").startswith("GoogleHC"):
            return Response(status=200)
        if settings.DEBUG:
            return redirect("/api/admin")

        if not request.user.is_authenticated:
            return login_index_view(request)

        return redirect("/")


class AdminCreationView(APIView):
    def get(self, request, format=None):
        import random
        import string

        try:
            User.objects.get(username="admin")
            return Response("User exists")

        except User.DoesNotExist:
            a = User(username="admin", email="admin@localhost")
            pw = "".join(
                random.choices(string.ascii_lowercase + string.digits + "!+-._", k=24)
            )
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


class WorkflowRunView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        flow = Workflow(should_run=True, user=request.user)
        flow.json = request.data.get("data", dict())
        flow.save()

        return Response()


class OldListImagesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        images = NodeImage.objects.all()
        images = [{"name": i.name, "labels": i.labels} for i in images]

        return Response(images)


class ListImagesView(ListAPIView):
    queryset = NodeImage.objects.all()
    serializer_class = NodeImageSerializer
    permission_classes = [IsAuthenticated]


class InspectImageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, name, format=None):
        try:
            image = NodeImage.objects.get(name=name)
        except:
            return Response(status=404)
        tags = image.tag_refs.all()
        tags = [{"name": i.name, "sha": i.sha} for i in tags]
        return Response(
            {
                "name": name,
                "labels": image.labels,
                "cmd": image.cmd,
                "env": image.env,
                "tags": tags,
            }
        )


class CommitView(APIView):
    def get(self, request, format=None):
        with open(".commit", "r") as f:
            return Response(f.read().replace("\n", ""))


class CronView(APIView):
    def post(self, request, format=None):
        from app.management.commands.cron import cron

        cron()
        return Response(status=200)


class GoogleStorageWebhook(APIView):
    def post(self, request):
        if request.headers.get("X-Goog-Channel-Token", "-") == os.environ.get(
            "gs_secret", "-"
        ):
            glob = Globals().instance
            glob.gs_webhook_fired = True
            glob.gs_webhook_working = True
            glob.save()

        return Response(status=200)


class FileUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def put(self, request, name=None, format=None):
        handle_uploaded_file(request)

        return Response(status=200)


class CheckAuthView(APIView):
    def get(self, request, format=None):
        u = request.user
        return Response(
            {"user": u.pk, "logged_in": u.is_authenticated or settings.DEBUG}
        )


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
        return Response(serializer.data)


class FinishUploadView(APIView):
    def post(self, request, format=None):
        return Response(finish_upload(request, get_upload(request)))


class FinalizeUploadView(APIView):
    def post(self, request, format=None):
        return Response(finalize_upload(request, get_upload(request)))


class UploadTreeView(APIView):
    def get(self, request, format=None):
        upload = get_upload(request)
        tree = file_tree("file", upload.uuid)
        return Response(tree)


class FileTypeListView(ListAPIView):
    queryset = FileType.objects.all()
    serializer_class = FileTypeSerializer
    permission_classes = [IsAuthenticated]


class CreateDownload(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        name = request.data.get("name", "")
        f_type = request.data.get("type", "")
        folder = Upload.for_name(name, f_type).make_download_link()

        url = reverse("download", kwargs={"name": folder, "filename": name})
        url = request.build_absolute_uri(url)
        return Response({"url": url})


class DownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, name="", filename="", format=None):

        path = settings.DOWNLOADS_DIR
        path = os.path.join(path, name)

        return FolderZipResponse(
            path, url_prefix=settings.DOWNLOADS_URL, filename=filename
        )


class NotificationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        id = request.GET.get("id", "")
        n = Notification.objects.get(pk=id)
        assert n.user == request.user
        n = NotificationSerializer(n).data
        return Response(n)

    def post(self, request, format=None):
        serializer = NotificationSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        n: Notification = serializer.save(user=request.user)
        n.notify()
        return Response(serializer.data)

    def delete(self, request, format=None):
        n = Notification.objects.get(pk=request.data["pk"])
        assert n.user == request.user
        n.delete()
        return Response()


class NamesForTypeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        f_type = request.GET.get("type", "file")

        names = []

        for u in Upload.objects.filter(file_type=f_type, is_newest=True):
            if u.name:
                names.append(u.name)

        return Response(names)


class CookieInfoView(APIView):
    def get(self, request, format=None):
        return Response(request.session.get("show_cookie_info", True))

    def post(self, request, format=None):
        request.session["show_cookie_info"] = False
        return Response(False)


class NotificationsList(ListAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        """
        This view should return a list of all the purchases
        for the currently authenticated user.
        """
        user = self.request.user
        return Notification.objects.filter(user=user)

    def delete(self, request, format=None):
        user = self.request.user
        ns = Notification.objects.filter(user=user)
        for n in ns:
            n.delete()
        return Response()
