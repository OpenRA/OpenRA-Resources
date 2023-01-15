from django.test import TestCase, Client, override_settings

from openra.tests.factories import UserFactory
#@override_settings(SITE_MAINTENANCE=False)
class TestRouteBase(TestCase):

    _route:str
    _client:Client

    def _get(self, client, data):
        self._client = client
        return client.get(self._route, data)

    def get(self, data={}):
        return self._get(Client(), data)

    def get_authed(self, data={}):
        client = Client()
        client.force_login(
            UserFactory()
        )
        return self._get(client, data)

    def _post(self, client, data):
        self._client = client
        return self._client.post(self._route, data)

    def post(self, data={}):
        return self._post(Client(), data)

    def post_authed(self, data={}):
        client = Client()
        client.force_login(
            UserFactory()
        )
        return self._post(client, data)

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

    def assert_is_maintenance(self,response):
        self.assertContains(
            response,
            'Site is under maintenance',
            status_code=503
        )

        return response
