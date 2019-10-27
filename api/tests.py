import random

from django.contrib.auth.models import Permission, User
from rest_framework.authtoken.models import Token

default_headers = {'content_type': 'application/json'}


def get_token_headers(token):
    return {**default_headers, 'HTTP_AUTHORIZATION': f'Token {token.key}'}


def create_credentials():
    password = list('Who is ready to make some science?'*int(random.random()*100))
    random.shuffle(password)
    return {
        'username': f'test-user{int(random.random() * 100)}',
        'password': ''.join(password)
    }


def create_user(**credentials):
    api_access = Permission.objects.get(codename='api_access')
    user = User.objects.create_user(**credentials)
    user.user_permissions.add(api_access)
    token = Token.objects.create(user=user)
    return user, get_token_headers(token)
