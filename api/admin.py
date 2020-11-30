from django.contrib import admin

from api.models import Log, Whitelist

# Register your models here.
admin.site.register(Log)
admin.site.register(Whitelist)
