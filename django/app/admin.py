from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(CronJob)
admin.site.register(NodeImage)
admin.site.register(NodeImageTag)
admin.site.register(Globals)
admin.site.register(Job)
