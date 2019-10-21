"""config URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from app.views import *
from django.views.generic.base import RedirectView
from django.views.generic import TemplateView

api = [
    path('list/', ListImagesView.as_view()),
    path('list/<path:name>/', InspectImageView.as_view()),
    path('upload/<str:name>/', FileUploadView.as_view(), name='upload'),
    path('upload/', FileUploadView.as_view()),
    path('check_auth/', CheckAuthView.as_view()),
    path('mail_test/', mail_test),
]

urlpatterns = [
    path('api/', include((api, 'app'), namespace='api')),
    path('.commit/', CommitView.as_view()),
    path('cron/', CronView.as_view()),
    path('admin/', admin.site.urls),
    path('createadmin/', AdminCreationView.as_view()),
    path('webhooks/gs_update/', GoogleStorageWebhook.as_view()),
    path('', IndexView.as_view(), name='index'),
    path('accounts/', include('django.contrib.auth.urls')),
]
