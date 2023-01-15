from django.test import TestCase, Client, override_settings

from openra.tests.factories import UserFactory

#@override_settings(SITE_MAINTENANCE=False)
class TestRouteBase(TestCase):

    _route:str

    def _get(self, client, data):
        return client.get(self._route, data)

    def get(self, data=[]):
        return self._get(Client(), data)

    def get_authed(self, data=[]):
        client = Client()
        client.force_login(
            UserFactory()
        )
        return self._get(client, data)

    def assert_ok_contains(self, response, content):
        self.assertContains(
            response,
            content,
            status_code=200
        )

        return response


    def assert_ok_contains_many(self, response, contents):
        for content in contents:
            self.assertContains(
                response,
                content,
                status_code=200
            )

        return response

    def assert_is_maintenance(self,response):
        self.assertContains(
            response,
            'Site is under maintenance',
            status_code=503
        )

        return response
