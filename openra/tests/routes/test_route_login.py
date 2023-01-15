from django.test import override_settings

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
