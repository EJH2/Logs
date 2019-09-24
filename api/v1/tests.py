from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status

from api.tests import create_user


class LogTestCase(TestCase):

    def setUp(self) -> None:
        self.credentials = {'username': 'test-user3', 'password': 'Who is ready to make some science?'}
        self.user, self.token_headers = create_user(**self.credentials)
        self.client = Client()
        self.client.login(**self.credentials)

    def _create_log(self):
        payload = {
            'type': 'rowboat',
            'url': 'https://mystb.in/raw/haseqocezu',
            'expires': '10min'
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
