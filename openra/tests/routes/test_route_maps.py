from django.test import Client, override_settings
import factory

from openra import content
from openra.tests.factories import MapsFactory, ScreenshotsFactory
from openra.tests.routes.test_route_base import TestRouteBase


class TestRouteMaps(TestRouteBase):

    _route = '/maps'

    def test_route_can_be_accessed_by_any_user(self):
        self.assert_contains(
            self.get(),
            [
                'Custom maps are stored in the user'
            ],
            title=content.titles['maps']
        )

    @override_settings(SITE_MAINTENANCE=True)
    def test_route_shows_maintenance_page(self):
        self.assert_is_maintenance(
            self.get()
        )

    def test_route_shows_maps(self):
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

    def test_route_shows_maps_as_json(self):
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
            self.get(route='/maps/json'),
            titles
        )

    def test_route_allows_any_sort_by_option(self):
        MapsFactory(map_hash='mymap'),
        MapsFactory(title='mymap'),
        MapsFactory(info='mymap'),
        MapsFactory(description='mymap'),
        MapsFactory(author='mymap')

        titles = []

        for sort in [
            'latest',
            'oldest',
            'title',
            'title_reversed',
            'players',
            'lately_commented',
            'rating',
            'views',
            'downloads',
            'revisions',
        ]:
            self.assert_contains(
                self.get({
                    'sort_by': sort
                })
            )
