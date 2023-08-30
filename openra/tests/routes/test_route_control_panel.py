from datetime import timedelta
from django.contrib import auth
from django.contrib.auth.base_user import make_password
from django.test import override_settings
from django.utils import timezone
from openra import content
from openra.helpers import merge_dicts
from openra.tests.factories import MapsFactory, UserFactory

from openra.tests.routes.test_route_base import TestRouteBase


class TestRouteControlPanel(TestRouteBase):

    _route = '/panel/'

    def test_route_can_be_accessed_by_an_authed_user(self):
        self.assert_contains(
            self.get_authed(),
            [
                'Sign out',
                'My Maps'
            ],
            title=content.titles['panel']
        )

    @override_settings(SITE_MAINTENANCE=True)
    def test_route_shows_maintenance_page(self):
        self.assert_is_maintenance(
            self.get()
        )

    def test_route_redirects_to_login_if_not_authed(self):
        response = self.get()

        self.assertEquals(
            302,
            response.status_code
        )

        self.assertEquals(
            '/login/',
            response.url
        )

    def test_route_will_show_a_users_maps(self):
        user = UserFactory()
        user.save()
        map = MapsFactory(
            user=user
        )
        map.save()

        map2 = MapsFactory(
            title='different_title'
        )
        map2.save()

        view = self.get_authed(
            user=user
        )

        self.assert_contains(
            view,
            [
                map.title,
                map.game_mod,
                map.author,
            ]
        )

        self.assert_doesnt_contain(
            view,
            [
                map2.title,
            ]
        )

    def test_route_will_show_16_user_maps(self):
        user = UserFactory()
        user.save()
        shown = []
        for i in range(20):
            map = MapsFactory(
                user=user,
                posted=timezone.now(),
                title="map_title_" + str(i) + "_"
            )
            map.save()
            shown.append(map)

        not_shown = []
        for i in range(20, 22):
            map = MapsFactory(
                user=user,
                posted=timezone.now() - timedelta(hours=1),
                title="map_title_" + str(i) + "_"
            )
            map.save()
            not_shown.append(map)

        view = self.get_authed(
            user=user
        )

        self.assert_contains(
            view,
            [
                '/panel/page/2/'
            ]
        )

        for map in shown:
            self.assert_contains(
                view,
                [
                    map.title,
                ]
            )

        for map in not_shown:
            self.assert_doesnt_contain(
                view,
                [
                    map.title,
                ]
            )

    def test_route_can_show_later_pages(self):
        user = UserFactory()
        user.save()
        not_shown = []
        for i in range(20):
            map = MapsFactory(
                user=user,
                posted=timezone.now(),
                title="map_title_" + str(i) + "_"
            )
            map.save()
            not_shown.append(map)

        shown = []
        for i in range(20, 22):
            map = MapsFactory(
                user=user,
                posted=timezone.now() - timedelta(hours=1),
                title="map_title_" + str(i) + "_"
            )
            map.save()
            shown.append(map)

        view = self.get_authed(
            route='/panel/page/2/',
            user=user,
        )

        self.assert_contains(
            view,
            [
                '/panel/page/1/'
            ]
        )

        for map in shown:
            self.assert_contains(
                view,
                [
                    map.title,
                ]
            )

        for map in not_shown:
            self.assert_doesnt_contain(
                view,
                [
                    map.title,
                ]
            )
