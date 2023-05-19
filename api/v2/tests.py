import random

import pendulum
from django.test import Client, TestCase
from django.urls import reverse
from rest_framework import status

from api.consts import all_types
from api.models import Whitelist
from api.tests import create_user, default_headers, create_credentials

import responses


def create_message(content):
    return [
        {
            'id': random.randint(1, 100),
            'author': {
                'id': 0,
                'username': 'test',
                'discriminator': '0',
                'avatar': None
            },
            'mentions': [],
            'content': ''.join(random.sample(content, len(content))),
            'timestamp': '2019-07-13T17:42:43.792000',
            'attachments': [],
            'embeds': []
        }
    ]


# Create your tests here.
class APITestCase(TestCase):

    def setUp(self) -> None:
        self.credentials = create_credentials()
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


class ArchiveTestCase(TestCase):

    def setUp(self) -> None:
        self.credentials = create_credentials()
        self.user, _ = create_user(**self.credentials)
        self.client = Client()
        self.client.login(**self.credentials)

    @responses.activate
    def test_archive_url(self):
        """Tests to see if the Archive API is functioning."""
        # Test archiving
        responses.add(responses.GET, 'https://example.com/log',
                      json=[
                          {
                              "id": "658136631949131787",
                              "author": {
                                  "id": "319313310514282506",
                                  "avatar": "e12bbe9ba8a06db42d2e9098caaa34af",
                                  "bot": False,
                                  "discriminator": "4379",
                                  "username": "Big Nibba"
                              },
                              "content": "Idk",
                              "timestamp": "2019-12-22T02:40:01.531Z",
                              "edited_timestamp": None,
                              "attachments": [],
                              "embeds": [],
                              "mentions": []
                          }
                      ])
        payload = {
            'type': random.choice(list(all_types.keys())),
            'url': 'https://example.com/log',  # This URL is for testing purposes only
            'expires': pendulum.now().add(minutes=10).isoformat()
        }
        archive_response = self.client.post(reverse('v2:archive'), data=payload)
        self.assertEqual(archive_response.status_code, status.HTTP_201_CREATED)
        signed_data = archive_response.json()['url'].rsplit('/', 1)[1]

        # Test un-archiving
        accepts_headers = {**default_headers, 'ACCEPTS': 'application/json'}
        un_archive_response = self.client.get(reverse('v2:un-archive', kwargs={'signed_data': signed_data}),
                                              **accepts_headers)
        self.assertEqual(un_archive_response.status_code, status.HTTP_302_FOUND)


class LogTestCase(TestCase):

    def setUp(self) -> None:
        self.credentials = create_credentials()
        self.user, self.token_headers = create_user(**self.credentials)
        self.client = Client()
        self.client.login(**self.credentials)

    def _create_log(self):
        messages = create_message(str(self.credentials))
        payload = {
            'type': random.choice(list(all_types.keys())),
            'messages': messages,
            'expires': pendulum.now().add(minutes=10).isoformat()
        }
        resp = self.client.post(reverse('v2:logs-list'), data=payload, **self.token_headers)
        return resp

    def test_log_create(self):
        """Tests to see if we can successfully create a log.

        This test will fail if either Redis or Celery have not been started!"""
        create_response = self._create_log()
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

    def test_log_retrieve(self):
        """Tests to see if we can retrieve the log we just created."""
        uuid = self._create_log().json()['uuid']
        retrieve_response = self.client.get(reverse('v2:logs-detail', kwargs={'pk': uuid}), **self.token_headers)
        self.assertEqual(retrieve_response.status_code, status.HTTP_200_OK)

    def test_log_destroy(self):
        """Tests to see if we can delete the log we just retrieved."""
        uuid = self._create_log().json()['uuid']
        destroy_response = self.client.delete(reverse('v2:logs-detail', kwargs={'pk': uuid}), **self.token_headers)
        self.assertEqual(destroy_response.status_code, status.HTTP_204_NO_CONTENT)

    def test_log_list(self):
        """Tests to see if we can list our logs after deleting one."""
        self._create_log()
        list_response = self.client.get(reverse('v2:logs-list'), **self.token_headers)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)


class WhitelistTestCase(TestCase):

    def setUp(self) -> None:
        self.credentials = create_credentials()
        self.user, self.token_headers = create_user(**self.credentials)
        self.client = Client()
        self.client.login(**self.credentials)
        self.log_type = random.choice(list(all_types.keys()))
        Whitelist.objects.create(log_type=self.log_type)

    def _create_log(self):
        messages = create_message(str(self.credentials))
        payload = {
            'type': self.log_type,
            'messages': messages,
            'expires': pendulum.now().add(minutes=10).isoformat()
        }
        resp = self.client.post(reverse('v2:logs-list'), data=payload, **self.token_headers)
        return resp

    def test_requires_whitelist(self):
        """Test to see if we can whitelist a log format to certain users."""
        # Test to see if the creation fails without being whitelisted
        non_whitelist_response = self._create_log()
        self.assertEqual(non_whitelist_response.status_code, status.HTTP_400_BAD_REQUEST)

        # Add user to whitelist
        whitelist = Whitelist.objects.get(log_type=self.log_type)
        whitelist.users.add(self.user)
        whitelist.save()

        # Test to see if creation succeeds after being whitelisted
        whitelist_response = self._create_log()
        self.assertEqual(whitelist_response.status_code, status.HTTP_201_CREATED)
