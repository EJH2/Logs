from django.contrib.auth.models import Permission, User
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token

default_headers = {'content_type': 'application/json'}


def get_token_headers(token):
    return {**default_headers, 'HTTP_AUTHORIZATION': f'Token {token.key}'}


def create_user(**credentials):
    api_access = Permission.objects.get(codename='api_access')
    user = User.objects.create_user(**credentials)
    user.user_permissions.add(api_access)
    token = Token.objects.create(user=user)
    return user, get_token_headers(token)


class APITestCase(TestCase):

    def setUp(self) -> None:
        self.credentials = {'username': 'test-user1', 'password': 'Who is ready to make some science?'}
        self.user, self.token_headers = create_user(**self.credentials)
        self.client = Client()
        self.client.login(**self.credentials)

    def test_requires_permissions(self):
        """Tests to see if the API requires permissions."""
        # Test if the API fails without authentication
        no_auth_response = Client().get(reverse('v2:logs-list'), **default_headers)
        self.assertNotEqual(no_auth_response.status_code, status.HTTP_200_OK)

        # Test if the API works with token authentication
        token_auth_response = self.client.get(reverse('v2:logs-list'), **self.token_headers)
        self.assertEqual(token_auth_response.status_code, status.HTTP_200_OK)

        # Test if the API works with session authentication
        session_auth_response = self.client.get(reverse('v2:logs-list'), **default_headers)
        self.assertEqual(session_auth_response.status_code, status.HTTP_200_OK)
