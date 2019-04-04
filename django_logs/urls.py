from django.contrib import admin
from django.urls import path, re_path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('view', views.view, name='view'),
    path('admin', admin.site.urls, name='admin'),

    re_path(r'temp/(?P<short_code>[\w]{5})?', views.temp, name='temp'),
    re_path(r'temp', views.temp, name='viewtemp'),

    re_path(r'(?P<short_code>[\w]{5})/raw', views.logs, kwargs={'raw': True}, name='raw'),
    re_path(r'(?P<short_code>[\w]{5})', views.logs, name='logs'),
]
