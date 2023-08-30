from django.test import Client, override_settings
import factory
from registration.forms import User

from openra import content
from openra.models import Reports
from openra.tests.factories import MapsFactory, ReportsFactory, ScreenshotsFactory, UserFactory
from openra.tests.routes.test_route_base import TestRouteBase


class TestRouteMapsUpdateMapInfo(TestRouteBase):

    _route = '/maps/{}/update-map-info'

    def test_route_can_be_accessed_by_any_user(self):
        map = MapsFactory()
        response = self.get_authed(
            {},
            None,
            self._route.format(map.id)
        )

        self.assertEquals(
            302,
            response.status_code
        )

        self.assertEquals(
            '/maps/' + str(map.id),
            response.url
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

        response = self.get(
            {},
            self._route.format(map.id)
        )

        self.assertEquals(
            302,
            response.status_code
        )

        self.assertEquals(
            '/login/',
            response.url
        )

    def test_map_info_can_be_updated_by_map_uploader(self):
        user = UserFactory()

        map = MapsFactory(
            user=user
        )

        response = self.post_authed(
            {
                'mapInfo': 'new map info',
            },
            user,
            self._route.format(map.id)
        )

        map.refresh_from_db()

        self.assertEquals(
            'new map info',
            map.info
        )

        self.assertEquals(
            302,
            response.status_code
        )

        self.assertEquals(
            '/maps/' + str(map.id),
            response.url
        )

    def test_map_info_can_be_updated_by_a_superuser(self):
        user = UserFactory(
            is_superuser=True
        )

        map = MapsFactory()

        response = self.post_authed(
            {
                'mapInfo': 'new map info',
            },
            user,
            self._route.format(map.id)
        )

        map.refresh_from_db()

        self.assertEquals(
            'new map info',
            map.info
        )

        self.assertEquals(
            302,
            response.status_code
        )

        self.assertEquals(
            '/maps/' + str(map.id),
            response.url
        )

    def test_map_info_cannot_be_updated_by_other_users(self):
        user = UserFactory()

        map = MapsFactory()

        response = self.post_authed(
            {
                'mapInfo': 'new map info',
            },
            user,
            self._route.format(map.id)
        )

        map.refresh_from_db()

        self.assertNotEquals(
            'new map info',
            map.info
        )

        self.assertEquals(
            302,
            response.status_code
        )

        self.assertEquals(
            '/maps/' + str(map.id),
            response.url
        )
