from django.shortcuts import render
from django.views import View as RegView
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User

# Create your views here.

from .images import list_images, inspect_image
from .models import *


class IndexView(APIView):
    def get(self, request, format=None):
        return Response(request.headers.get("X-Forwarded-Proto", "None") + "Bio Node")


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


class ListImagesView(APIView):
    def get(self, request, format=None):
        return Response(list_images())


class InspectImageView(APIView):
    def get(self, request, name, format=None):
        return Response(inspect_image(name))


class CommitView(APIView):
    def get(self, request, format=None):
        with open(".commit", "r") as f:
            return Response(f.read().replace('\n', ''))
