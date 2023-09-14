from django.test import Client, override_settings
import factory
from registration.forms import User

from openra import content
from openra.models import Reports
from openra.tests.factories import MapsFactory, ReportsFactory, ScreenshotsFactory, UserFactory
from openra.tests.routes.test_route_base import TestRouteBase


class TestRouteUserActionsBlocked(TestRouteBase):

    _route = '/accounts/actions-blocked'

    def test_route_can_be_accessed_by_any_user(self):
        user = UserFactory()

        response = self.get_authed(
            {},
            user
        )

        self.assert_contains(
            response,
            [

                'User accounts must be one day old'
            ],
            title=content.titles['user_actions_blocked']
        )

    @override_settings(SITE_MAINTENANCE=True)
    def test_route_shows_maintenance_page(self):
        map = MapsFactory()
        self.assert_is_maintenance(
            self.get(
                {},
                self._route.format(map.id)
            ),
        )

    def test_route_redirects_to_login_if_not_authed(self):
        map = MapsFactory()

        response = self.get()

        self.assertEquals(
            302,
            response.status_code
        )

        self.assertEquals(
            '/login/',
            response.url
        )

    def test_will_show_time_remaining_if_blocked(self):
        user = UserFactory()

        response = self.get_authed(
            {},
            user
        )

        self.assert_contains(
            response,
            [
                '24 hours'
            ],
            title=content.titles['user_actions_blocked']
        )

    def test_can_show_when_block_it_over(self):
        user = self.create_old_user()

        response = self.get_authed(
            {},
            user
        )

        self.assert_contains(
            response,
            [
                'block is over'
            ],
            title=content.titles['user_actions_blocked']
        )
