from django.shortcuts import render
from django.views import View as RegView
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView

# Create your views here.

from .images import list_images, inspect_image


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
