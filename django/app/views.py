from django.shortcuts import render
from django.views import View as RegView
from django.http import HttpResponse, Http404
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User

# Create your views here.

from .models import *


class IndexView(APIView):
    def get(self, request, format=None):
        return Response("Bio Node")


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
        images = NodeImage.objects.all()
        images = [
            {
                'name': i.name,
                'labels': i.labels
            } for i in images
        ]

        return Response(images)


class InspectImageView(APIView):
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
            'tags': tags
        })


class CommitView(APIView):
    def get(self, request, format=None):
        with open(".commit", "r") as f:
            return Response(f.read().replace('\n', ''))
