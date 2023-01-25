from django.contrib import auth
from django.contrib.auth.base_user import make_password
from django.test import override_settings
from openra import content
from openra.helpers import merge_dicts
from openra.tests.factories import UserFactory

from openra.tests.routes.test_route_base import TestRouteBase


class TestRouteLogout(TestRouteBase):

    _route = '/logout/'

    def test_route_can_be_accessed_by_an_authed_user(self):
        self.assert_contains(
            self.get_authed(),
            [
                'Sign Out',
                '/logout/',
                'POST'
            ],
            title=content.titles['logout']
        )

    @override_settings(SITE_MAINTENANCE=True)
    def test_route_shows_maintenance_page(self):
        self.assert_is_maintenance(
            self.get()
        )

        self.assert_is_maintenance(
            self.post()
        )

    def test_route_redirects_to_home_if_not_authed(self):
        response = self.get()

        self.assertEquals(
            302,
            response.status_code
        )

        self.assertEquals(
            '/',
            response.url
        )

    def test_post_logs_out_user_and_redirects_to_home(self):
        response = self.post_authed()

        self.assertEquals(
            302,
            response.status_code
        )

        self.assertEquals(
            '/',
            response.url
        )

        self.assertFalse(
            auth.get_user(self._client).is_authenticated()
        )
