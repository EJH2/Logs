from django.shortcuts import redirect
from django.urls import include, re_path, path

from api import views


def redirect_to_v1():
    return redirect('v1:schema-redoc')


urlpatterns = [
    path('', lambda request: redirect_to_v1()),
    re_path(r'^(?P<version>v1|v2)/get_token', lambda request, version: views.get_token(request), name='get_token'),
    re_path(r'^v1/', include(('api.v1.urls', 'v1'), namespace='v1')),
    re_path(r'^v2/', include(('api.v2.urls', 'v2'), namespace='v2')),
]
