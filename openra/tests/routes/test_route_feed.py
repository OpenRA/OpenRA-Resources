from django.test import override_settings
import factory

from openra.tests.factories import MapsFactory, ScreenshotsFactory
from openra.tests.routes.test_route_base import TestRouteBase

class TestRouteHome(TestRouteBase):

    _route = '/news/feed.rss'

    def test_route_can_be_accessed_by_any_user(self):
        self.assert_contains(
            self.get(),
            ['OpenRA Resource Center - RSS Feed']
        )

    @override_settings(SITE_MAINTENANCE=True)
    def test_route_shows_maintenance_page(self):
        self.assert_is_maintenance(
            self.get()
        )

    def test_route_shows_latest_maps(self):
        map_models = factory.create_batch(MapsFactory, 20)

        response = self.assert_contains(
            self.get(),
            ['OpenRA Resource Center - RSS Feed']
        )

        for model in map_models:
            self.assert_contains(
                response,
                [
                    f'<title>{model.title}</title>'
                ]
            )

