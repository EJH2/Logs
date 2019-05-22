from django.contrib import admin

# Register your models here.
from django_logs.models import Log

admin.site.register(Log)
