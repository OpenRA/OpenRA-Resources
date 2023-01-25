from django.test import override_settings
import factory

from openra.tests.factories import ScreenshotsFactory
from openra.tests.routes.test_route_base import TestRouteBase


class TestRouteHome(TestRouteBase):

    _route = '/'

    def test_route_can_be_accessed_by_any_user(self):
        self.assert_contains(
            self.get(),
            ['Share your Maps!']
        )

    @override_settings(SITE_MAINTENANCE=True)
    def test_route_shows_maintenance_page(self):
        self.assert_is_maintenance(
            self.get()
        )

    def test_route_shows_latest_screenshots(self):
        screenshot_models = factory.create_batch(ScreenshotsFactory, 5)

        response = self.assert_contains(
            self.get(),
            ['Share your Maps!']
        )

        for model in screenshot_models:
            self.assert_contains(
                response,
                [
                    f'/maps/{model.ex_id}/',
                    f'/screenshots/{model.id}/'
                ]
            )
