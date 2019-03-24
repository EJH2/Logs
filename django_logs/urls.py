from django.urls import path, re_path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('view', views.view, name='view'),
    re_path(r'(?P<short_code>[\w]{5})/raw', views.logs, kwargs={'raw': True}, name='raw'),
    re_path(r'(?P<short_code>[\w]{5})', views.logs, name='logs'),
]

handler404 = views.handler404
handler500 = views.handler500
