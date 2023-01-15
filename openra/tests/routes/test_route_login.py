from django.contrib.auth.base_user import make_password
from django.test import override_settings
from openra import content
from openra.helpers import merge_dicts
from openra.tests.factories import UserFactory

from openra.tests.routes.test_route_base import TestRouteBase

class TestRouteLogin(TestRouteBase):

    _route = '/login/'

    def test_route_can_be_accessed_by_an_unauthed_user(self):
        self.assert_ok_contains_many(
            self.get(),
            [
                'Sign In',
                'ora_username',
                'ora_password',
                '/login/',
                'POST'
            ]
        )

    @override_settings(SITE_MAINTENANCE=True)
    def test_route_shows_maintenance_page(self):
        self.assert_is_maintenance(
            self.get()
        )

        self.assert_is_maintenance(
            self.post()
        )

    def test_route_redirects_to_home_if_authed(self):
        response = self.get_authed()

        self.assertEquals(
            302,
            response.status_code
        )

        self.assertEquals(
            '/',
            response.url
        )

    def _send_valid_post(self, data={}):
        user = UserFactory(
            password=make_password('password')
        )
        return self.post(merge_dicts({
            'ora_username':user.username,
            'ora_password':'password'
        }, data))

    def test_post_logs_in_user_and_redirects_to_home(self):
        response = self._send_valid_post()

        self.assertEquals(
            302,
            response.status_code
        )

        self.assertEquals(
            '/',
            response.url
        )

        self.assertTrue(
            self._client.session.get_expire_at_browser_close()
        )

    def test_post_preserves_session_if_remember_is_ticked(self):
        self._send_valid_post({
            'ora_remember':'Yes'
        })

        self.assertFalse(
            self._client.session.get_expire_at_browser_close()
        )

    def test_post_can_show_inactive_error(self):
        user = UserFactory(
            is_active=False,
            password=make_password('password')
        )

        self.assert_ok_contains(
            self.post({
                'ora_username':user.username,
                'ora_password':'password'
            }),
            content.auth['inactive']
        )

    def test_post_can_show_incorrect_credentials_error(self):
        self.assert_ok_contains(
            self._send_valid_post({
                'ora_password':'wrong'
            }),
            content.auth['incorrect']
        )
