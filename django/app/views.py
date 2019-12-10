import os
from django.shortcuts import render, redirect
from django.views import View as RegView
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.conf import settings
from django.urls import reverse
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.status import *
from rest_framework.views import APIView
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
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
    clear_upload,
)
from .serializers import *
from .events import send_event


@login_required
def login_index_view(request):
    return Response()


class IndexView(APIView):
    def get(self, request, format=None):
        if request.headers.get("User-Agent", "").startswith("GoogleHC"):
            return Response(status=HTTP_200_OK)
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
        pk = request.GET.get("pk", "")
        if pk:
            flow = Workflow.objects.get(pk=pk)
            assert request.user.is_superuser or flow.user == request.user
        else:
            flow = Workflow.objects.get(should_run=False, name=name)

        return Response(flow.json)

    def post(self, request, format=None):
        name = request.data.get("name", "")
        try:
            flow = Workflow.objects.get(should_run=False, name=name)
        except:
            flow = Workflow(name=name)
        flow.json = request.data.get("data", dict())
        flow.user = request.user
        flow.save()

        return Response()


class WorkflowView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, name, format=None):
        flow = Workflow.objects.get(pk=name)
        if flow.user != request.user and not request.user.is_superuser:
            return Response(status=HTTP_403_FORBIDDEN)

        serializer = WorkflowSerializer(flow)

        return Response(serializer.data)


class WorkflowsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        from django.db.models import Q

        if request.user.is_superuser:
            flows = Workflow.objects.all()
        else:
            flows = Workflow.objects.filter(Q(user=request.user) | Q(should_run=False))
        serializer = WorkflowSerializer(flows, many=True)

        return Response(serializer.data)


class JobView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        name = request.GET.get("name", "")
        job = Job.objects.get(uuid=name)

        job = JobSerializer(job)

        return Response(job.data)


class JobLogsView(APIView):
    def get(self, request, format=None):
        name = request.GET.get("name", "")
        as_json = request.GET.get("json", False)

        job = Job.objects.get(uuid=name)
        logs = job.logs

        if as_json:
            return Response(logs)
        else:
            response = HttpResponse(logs, content_type='text/plain')
            response['Content-Disposition'] = "attachment; filename=%s.log" % name
            return response


class WorkflowRunView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        flow = Workflow(should_run=True, user=request.user)
        flow.json = request.data.get("data", dict())
        flow.prepare_workflow()

        return Response(flow.pk)


class WorkflowNameView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        old = request.data.get("pk", "")
        new = request.data.get("name", "")

        flow = Workflow.objects.get(pk=old)
        if request.user.is_superuser or flow.user == request.user:
            flow.name = new
            flow.save()

        return Response()


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
            return Response(status=HTTP_404_NOT_FOUND)
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


class ImportImageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        from .images import import_image

        name = request.data.get("name", "")
        tag = request.data.get("tag", "")

        if tag:
            import_image(name, tag, user=request.user)
        else:
            import_image(name, user=request.user)

        send_event("image-imported", name)

        return Response()


class UpdateImageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        from .images import update_image

        name = request.data.get("name", "")

        update_image(name, user=request.user)

        send_event("image-imported", name)

        return Response()


class ChangeImageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        from .images import change_image

        name = request.data.get("name", "")
        data = request.data.get("data", {})

        change_image(name, data=data, user=request.user)

        send_event("image-imported", name)

        return Response()


class DeleteImageView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, format=None):
        from .images import import_image

        name = request.data.get("name", "")
        image = NodeImage.objects.get(name=name)
        if image.imported_by == request.user or request.user.is_superuser:
            image.delete()
        else:
            Notification.send(
                request.user, "Permissions", "You have insufficient permissions.", 10,
            )
            return Response(status=HTTP_403_FORBIDDEN)

        return Response()


class CommitView(APIView):
    def get(self, request, format=None):
        with open(".commit", "r") as f:
            return Response(f.read().replace("\n", ""))


class CronView(APIView):
    def post(self, request, format=None):
        from app.management.commands.cron import cron

        cron()
        return Response(status=HTTP_200_OK)


class GoogleStorageWebhook(APIView):
    def post(self, request):
        if request.headers.get("X-Goog-Channel-Token", "-") == os.environ.get(
            "gs_secret", "-"
        ):
            glob = Globals().instance
            glob.gs_webhook_fired = True
            glob.gs_webhook_working = True
            glob.save()

        return Response(status=HTTP_200_OK)


class FileUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def put(self, request, name=None, format=None):
        handle_uploaded_file(request)

        return Response(status=HTTP_200_OK)


class CheckAuthView(APIView):
    def get(self, request, format=None):
        u = request.user
        return Response(Permissions.from_user(u))


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

    def remove(self, request):
        clear_upload(request)
        return Response()


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


class LoginOverride(LoginView):
    def get(self, request, *args, **kwargs):
        if request.GET.get("next", None) is None:
            return HttpResponseRedirect(request.path_info + "?next=/")

        return super().get(request, *args, **kwargs)


class RandomNameView(APIView):
    def get(self, request, format=None):
        from .util import default_name

        return Response(default_name())
