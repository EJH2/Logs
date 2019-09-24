import random

from django.test import Client, TestCase
from django.urls import reverse
from rest_framework import status

from api.consts import all_types
from api.tests import create_user, default_headers


def create_message(content):
    return [
        {
            'id': 0,
            'author': {
                'id': 0,
                'username': 'test',
                'discriminator': '0000',
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
class ArchiveTestCase(TestCase):

    def setUp(self) -> None:
        self.credentials = {'username': 'test-user2', 'password': 'Who is ready to make some science?'}
        self.user, _ = create_user(**self.credentials)
        self.client = Client()
        self.client.login(**self.credentials)

    def test_archive_url(self):
        """Tests to see if the Archive API is functioning."""
        # Test archiving
        payload = {
            'type': random.choice(list(all_types.keys())),
            'url': 'https://mystb.in/raw/nihubativo',  # This URL is for testing purposes only
            'expires': '10min'
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
        self.credentials = {'username': 'test-user3', 'password': 'Who is ready to make some science?'}
        self.user, self.token_headers = create_user(**self.credentials)
        self.client = Client()
        self.client.login(**self.credentials)

    def _create_log(self):
        messages = create_message(str(self.credentials))
        payload = {
            'type': random.choice(list(all_types.keys())),
            'messages': messages,
            'expires': '10min'
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
