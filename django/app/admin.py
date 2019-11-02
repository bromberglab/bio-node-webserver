from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(CronJob)
admin.site.register(NodeImage)
admin.site.register(NodeImageTag)
admin.site.register(Globals)
admin.site.register(Job)
admin.site.register(Upload)
admin.site.register(FileType)
admin.site.register(Workflow)
admin.site.register(Download)
