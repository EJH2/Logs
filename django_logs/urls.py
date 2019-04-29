from django.contrib import admin
from django.urls import path, re_path, include

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login', views.login),
    path('view', views.view, name='view'),
    path('admin', admin.site.urls, name='admin'),
    path('accounts/', include('allauth.urls')),

    re_path('api', views.api, name='api'),

    re_path(r'(?P<short_code>[\w]{5})/raw', views.logs, kwargs={'raw': True}, name='raw'),
    re_path(r'(?P<short_code>[\w]{5})', views.logs, name='logs'),
]

handler404 = views.handle404
handler500 = views.handle500
