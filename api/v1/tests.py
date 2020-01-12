import pendulum
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status

from api.models import Whitelist
from api.tests import create_user, default_headers, create_credentials


class APITestCase(TestCase):

    def setUp(self) -> None:
        self.credentials = create_credentials()
        self.user, self.token_headers = create_user(**self.credentials)
        self.client = Client()
        self.client.login(**self.credentials)

    def test_requires_permissions(self):
        """Tests to see if the API requires permissions."""
        # Test if the API fails without authentication
        no_auth_response = Client().get(reverse('v1:logs-list'), **default_headers)
        self.assertNotEqual(no_auth_response.status_code, status.HTTP_200_OK)

        # Test if the API works with token authentication
        token_auth_response = self.client.get(reverse('v1:logs-list'), **self.token_headers)
        self.assertEqual(token_auth_response.status_code, status.HTTP_200_OK)

        # Test if the API works with session authentication
        session_auth_response = self.client.get(reverse('v1:logs-list'), **default_headers)
        self.assertEqual(session_auth_response.status_code, status.HTTP_200_OK)


class LogTestCase(TestCase):

    def setUp(self) -> None:
        self.credentials = create_credentials()
        self.user, self.token_headers = create_user(**self.credentials)
        self.client = Client()
        self.client.login(**self.credentials)

    def _create_log(self):
        payload = {
            'type': 'rowboat',
            'url': 'https://mystb.in/raw/haseqocezu',
            'expires': pendulum.now().add(minutes=10)
        }
        resp = self.client.post(reverse('v1:logs-list'), data=payload, **self.token_headers)
        return resp

    def test_log_create(self):
        """Tests to see if we can successfully create a log.

        This test will fail if either Redis or Celery have not been started!"""
        create_response = self._create_log()
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

    def test_log_retrieve(self):
        """Tests to see if we can retrieve the log we just created."""
        uuid = self._create_log().json()['uuid']
        retrieve_response = self.client.get(reverse('v1:logs-detail', kwargs={'pk': uuid}), **self.token_headers)
        self.assertEqual(retrieve_response.status_code, status.HTTP_200_OK)

    def test_log_destroy(self):
        """Tests to see if we can delete the log we just retrieved."""
        uuid = self._create_log().json()['uuid']
        destroy_response = self.client.delete(reverse('v1:logs-detail', kwargs={'pk': uuid}), **self.token_headers)
        self.assertEqual(destroy_response.status_code, status.HTTP_204_NO_CONTENT)

    def test_log_list(self):
        """Tests to see if we can list our logs after deleting one."""
        self._create_log()
        list_response = self.client.get(reverse('v1:logs-list'), **self.token_headers)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)


class WhitelistTestCase(TestCase):

    def setUp(self) -> None:
        self.credentials = create_credentials()
        self.user, self.token_headers = create_user(**self.credentials)
        self.client = Client()
        self.client.login(**self.credentials)
        Whitelist.objects.create(log_type='rowboat')

    def _create_log(self):
        payload = {
            'type': 'rowboat',
            'url': 'https://mystb.in/raw/haseqocezu',
            'expires': pendulum.now().add(minutes=10)
        }
        resp = self.client.post(reverse('v1:logs-list'), data=payload, **self.token_headers)
        return resp

    def test_requires_whitelist(self):
        """Test to see if we can whitelist a log format to certain users."""
        # Test to see if the creation fails without being whitelisted
        non_whitelist_response = self._create_log()
        self.assertEqual(non_whitelist_response.status_code, status.HTTP_400_BAD_REQUEST)

        # Add user to whitelist
        whitelist = Whitelist.objects.get(log_type='rowboat')
        whitelist.users.add(self.user)
        whitelist.save()

        # Test to see if creation succeeds after being whitelisted
        whitelist_response = self._create_log()
        self.assertEqual(whitelist_response.status_code, status.HTTP_201_CREATED)
