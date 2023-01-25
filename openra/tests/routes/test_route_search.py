from django.test import Client, override_settings
import factory

from openra import content
from openra.tests.factories import MapsFactory, ScreenshotsFactory
from openra.tests.routes.test_route_base import TestRouteBase


class TestRouteHome(TestRouteBase):

    _route = '/search/mymap'

    def test_route_can_be_accessed_by_any_user(self):
        self.assert_contains(
            self.get(),
            [
                'Nothing found'
            ],
            title=content.titles['search']
        )

    @override_settings(SITE_MAINTENANCE=True)
    def test_route_shows_maintenance_page(self):
        self.assert_is_maintenance(
            self.get()
        )

    def test_route_redirects_when_no_query(self):
        response = Client().get('/search/')

        self.assertEquals(
            302,
            response.status_code
        )

        self.assertEquals(
            '/',
            response.url
        )

    def test_route_shows_search_result_maps(self):
        maps = [
            MapsFactory(map_hash='mymap'),
            MapsFactory(title='mymap'),
            MapsFactory(info='mymap'),
            MapsFactory(description='mymap'),
            MapsFactory(author='mymap')
        ]

        titles = []

        for map_model in maps:
            titles.append(map_model.title)

        self.assert_contains(
            self.get(),
            titles
        )
