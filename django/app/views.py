from django.shortcuts import render
from django.views import View as RegView
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView

# Create your views here.

from .images import list_images


class ListImagesView(APIView):
    def get(self, request, format=None):
        return Response(list_images())
