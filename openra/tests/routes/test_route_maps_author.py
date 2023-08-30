from django.test import Client, override_settings
import factory
from registration.forms import User

from openra import content
from openra.tests.factories import MapsFactory, ScreenshotsFactory, UserFactory
from openra.tests.routes.test_route_base import TestRouteBase


class TestRouteMapsAuthor(TestRouteBase):

    _route = '/maps/author/'

    def test_route_can_be_accessed_by_any_user(self):
        author = UserFactory()
        self.assert_contains(
            self.get(
                {},
                self._route + author.username
            ),
            [
                'Found 0 maps authored by'
            ],
            title=content.titles['maps_author'].format(author.username)
        )

    @override_settings(SITE_MAINTENANCE=True)
    def test_route_shows_maintenance_page(self):
        author = UserFactory()
        self.assert_is_maintenance(
            self.get(
                {},
                self._route + author.username
            ),
        )

    def test_route_shows_maps(self):
        author = UserFactory()
        maps = [
            MapsFactory(map_hash='mymap', author=author.username),
            MapsFactory(title='mymap', author=author.username),
            MapsFactory(info='mymap', author=author.username),
            MapsFactory(description='mymap', author=author.username),
        ]

        titles = []

        for map_model in maps:
            titles.append(map_model.title)

        self.assert_contains(
            self.get({}, self._route + author.username),
            titles
        )

    def test_route_allows_any_sort_by_option(self):
        author = UserFactory()
        MapsFactory(map_hash='mymap', author=author.username),
        MapsFactory(title='mymap', author=author.username),
        MapsFactory(info='mymap', author=author.username),
        MapsFactory(description='mymap', author=author.username),

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
                    self._route + author.username
                ),
                'Found 4 maps authored by'
            )
