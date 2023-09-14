from django.test import TestCase, Client, override_settings

from openra.tests.factories import UserFactory
from django.utils import timezone


@override_settings(SITE_MAINTENANCE=False)
class TestRouteBase(TestCase):

    _route: str
    _client: Client

    def _get(self, client, data, route):
        self._client = client
        return client.get(
            route if route else self._route,
            data
        )

    def get(self, data={}, route=None):
        return self._get(Client(), data, route)

    def get_authed(self, data={}, user=None, route=None):
        client = Client()
        client.force_login(
            user if user else UserFactory()
        )
        return self._get(client, data, route)

    def _post(self, client, data, route):
        self._client = client
        return client.post(
            route if route else self._route,
            data
        )

    def post(self, data={}, route=None):
        return self._post(Client(), data, route)

    def post_authed(self, data={}, user=None, route=None):
        client = Client()
        client.force_login(
            user if user else UserFactory()
        )
        return self._post(client, data, route)

    def create_old_user(self):
        return UserFactory(
            date_joined=timezone.datetime(1996, 11, 29, 0, 0)
        )

    def assert_contains(self, response, contents=[],
                        status_code=200,
                        title=''
                        ):
        if title != '':
            contents.append(f'<title>OpenRA Resource Center - {title}</title>')
        for content in contents:
            self.assertContains(
                response,
                content,
                status_code=status_code
            )

        return response

    def assert_doesnt_contain(self, response, contents=[]):
        decoded_response = response.content.decode('utf-8')
        for content in contents:
            self.assertNotIn(
                content,
                decoded_response
            )

        return response

    def assert_is_maintenance(self, response):
        self.assertContains(
            response,
            'Site is under maintenance',
            status_code=503
        )

        return response
