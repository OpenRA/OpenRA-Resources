from django.test import Client, override_settings
import factory
from registration.forms import User

from openra import content
from openra.tests.factories import MapsFactory, ScreenshotsFactory, UserFactory
from openra.tests.routes.test_route_base import TestRouteBase


class TestRouteMapsUploader(TestRouteBase):

    _route = '/maps/uploader/'

    def test_route_can_be_accessed_by_any_user(self):
        uploader = UserFactory()
        self.assert_contains(
            self.get(
                {},
                self._route + uploader.username
            ),
            [
                'Found 0 maps uploaded by'
            ],
            title=content.titles['maps_uploader'].format(uploader.username)
        )

    @override_settings(SITE_MAINTENANCE=True)
    def test_route_shows_maintenance_page(self):
        uploader = UserFactory()
        self.assert_is_maintenance(
            self.get(
                {},
                self._route + uploader.username
            ),
        )

    def test_route_shows_maps(self):
        uploader = UserFactory()
        maps = [
            MapsFactory(map_hash='mymap', user=uploader),
            MapsFactory(title='mymap', user=uploader),
            MapsFactory(info='mymap', user=uploader),
            MapsFactory(description='mymap', user=uploader),
        ]

        titles = []

        for map_model in maps:
            titles.append(map_model.title)

        self.assert_contains(
            self.get({}, self._route + uploader.username),
            titles
        )

    def test_route_allows_any_sort_by_option(self):
        uploader = UserFactory()
        MapsFactory(map_hash='mymap', user=uploader),
        MapsFactory(title='mymap', user=uploader),
        MapsFactory(info='mymap', user=uploader),
        MapsFactory(description='mymap', user=uploader),

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
                },
                    self._route + uploader.username
                ),
                'Found 4 maps uploaded by'
            )
