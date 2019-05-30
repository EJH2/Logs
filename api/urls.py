from django.urls import re_path, path
from rest_framework_swagger.views import get_swagger_view

from api import views

urlpatterns = [
    path('', get_swagger_view(title='Django Logs API')),
    path('logs/', views.LogView.as_view()),
    path('logs/create/', views.LogCreate.as_view()),
    re_path(r'logs/delete/(?P<short_code>[\w]{5})?', views.LogDestroy.as_view()),
    re_path(r'logs/(?P<short_code>[\w]{5})?', views.LogRead.as_view()),
    re_path(r'traceback/', views.traceback, name='traceback'),
]
