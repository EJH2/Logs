from allauth.account.views import login, signup, logout, email_verification_sent, confirm_email
from allauth.socialaccount.providers.discord.views import oauth2_login, oauth2_callback
from django.contrib import admin
from django.urls import path, re_path, include

from django_logs import api
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('view', views.view, name='view'),
    path('admin', admin.site.urls, name='admin'),

    path('celery-progress/', include('celery_progress.urls')),
    path('tb', views.traceback, name='traceback'),

    path('login', login, name='account_login'),
    path('login/discord', oauth2_login, name='discord_login'),
    path('login/callback', oauth2_callback, name='discord_callback'),
    path('signup', signup, name='account_signup'),
    path('logout', logout, name='account_logout'),
    path('verifyemail', email_verification_sent, name='account_email_verification_sent'),
    re_path('verifyemail/(?P<key>[\w\-:]+)', confirm_email, name='account_confirm_email'),

    re_path('api', api.api, name='api'),

    re_path(r'(?P<short_code>[\w]{5})/raw', views.logs, kwargs={'raw': True}, name='raw'),
    re_path(r'(?P<short_code>[\w]{5})', views.logs, name='logs'),
]

handler404 = views.handle404
handler500 = views.handle500
