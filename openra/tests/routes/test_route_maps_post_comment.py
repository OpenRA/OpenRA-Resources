from django.test import Client, override_settings
import factory
from registration.forms import User

from openra import content
from openra.models import Comments, Reports
from openra.tests.factories import MapsFactory, ReportsFactory, ScreenshotsFactory, UserFactory
from openra.tests.routes.test_route_base import TestRouteBase


class TestRouteMapsPostComment(TestRouteBase):

    _route = '/maps/{}/post-comment'

    def test_route_can_be_accessed_by_any_user(self):
        user = self.create_old_user()
        map = MapsFactory()

        response = self.post_authed(
            {
                'comment': 'Comment'
            },
            user,
            self._route.format(map.id)
        )

        self.assertEquals(
            302,
            response.status_code
        )

        self.assertEquals(
            '/maps/' + str(map.id) + '/#comments',
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

        response = self.post(
            {
                'comment': 'Comment'
            },
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

        self.assertEquals(
            0,
            Comments.objects.count()
        )

    def test_it_redirects_to_actions_blocked_if_new_account(self):
        map = MapsFactory()

        response = self.post_authed(
            {
                'comment': 'Comment'
            },
            None,
            self._route.format(map.id)
        )

        self.assertEquals(
            302,
            response.status_code
        )

        self.assertEquals(
            '/accounts/actions-blocked',
            response.url
        )

        self.assertEquals(
            0,
            Comments.objects.count()
        )

    def test_it_can_add_a_comment(self):
        user = self.create_old_user()
        map = MapsFactory()

        self.assertEquals(
            0,
            Comments.objects.count()
        )

        response = self.post_authed(
            {
                'comment': 'Comment'
            },
            user,
            self._route.format(map.id)
        )

        self.assertEquals(
            302,
            response.status_code
        )

        self.assertEquals(
            '/maps/' + str(map.id) + '/#comments',
            response.url
        )

        self.assertEquals(
            1,
            Comments.objects.count()
        )
