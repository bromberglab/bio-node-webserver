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
    path("file_types/", FileTypeListView.as_view()),
    path("list/", ListImagesView.as_view()),
    path("list/<path:name>/", InspectImageView.as_view()),
    path("import_image/", ImportImageView.as_view()),
    path("update_image/", UpdateImageView.as_view()),
    path("change_image/", ChangeImageView.as_view()),
    path("delete_image/", DeleteImageView.as_view()),
    path("upload/<str:name>/", FileUploadView.as_view(), name="upload"),
    path("upload/", FileUploadView.as_view()),
    path("my_upload/", MyUploadView.as_view({"get": "retrieve", "post": "update"})),
    path("upload_tree/", UploadTreeView.as_view()),
    path("finish_upload/", FinishUploadView.as_view()),
    path("finalize_upload/", FinalizeUploadView.as_view()),
    path("check_auth/", CheckAuthView.as_view()),
    path("workflow_storage/", WorkflowStorageView.as_view()),
    path("workflow_run/", WorkflowRunView.as_view()),
    path("job/", JobView.as_view()),
    path("create_download/", CreateDownload.as_view()),
    path(
        "download/<str:name>/<str:filename>/", DownloadView.as_view(), name="download"
    ),
    path("names_for_type/", NamesForTypeView.as_view()),
    path("show_cookie_info/", CookieInfoView.as_view()),
    path("notification/", NotificationView.as_view()),
    path("notifications/", NotificationsList.as_view()),
]

main = [
    path("v1/", include(api)),
    path(".commit/", CommitView.as_view()),
    path("cron/", CronView.as_view()),
    path("admin/login/", RedirectView.as_view(url="/api/accounts/login")),
    path("admin/", admin.site.urls),
    path("createadmin/", AdminCreationView.as_view()),
    path("webhooks/gs_update/", GoogleStorageWebhook.as_view()),
    path("", IndexView.as_view(), name="index"),
    path("accounts/profile/", RedirectView.as_view(url="/")),
    path("accounts/", include("django.contrib.auth.urls")),
]

urlpatterns = [
    path("api/", include(main)),
]
