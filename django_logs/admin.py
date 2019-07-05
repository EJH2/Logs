from django.contrib import admin

# Register your models here.
from django_logs.models import Log, Job

admin.site.register(Log)
admin.site.register(Job)
