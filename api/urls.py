from django.urls import re_path, path
from rest_framework.documentation import include_docs_urls

from api import views

description = """
API provided to logged-in users. In order to use this API, users must authenticate with: 
`Authorization: Token xxxxxxxxxxxxxxxxxxxx` in the headers of the request.
"""

urlpatterns = [
    path('', include_docs_urls(title='Django Logs API', public=False, description=description)),
    re_path('logs(?:/)?$', views.LogView.as_view()),
    re_path('token(?:/)?$', views.GetToken.as_view(), name='get_token'),
    re_path(r'logs/(?P<short_code>[\w]{5})(?:/)?$', views.LogRead.as_view()),
    re_path(r'traceback(?:/)?$', views.GetTraceback.as_view(), name='traceback'),
]
