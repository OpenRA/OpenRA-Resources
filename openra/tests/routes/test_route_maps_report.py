from django.test import Client, override_settings
import factory
from registration.forms import User

from openra import content
from openra.models import Reports
from openra.tests.factories import MapsFactory, ReportsFactory, ScreenshotsFactory, UserFactory
from openra.tests.routes.test_route_base import TestRouteBase


class TestRouteMapsReport(TestRouteBase):

    _route = '/maps/{}/report'

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

    def test_a_report_can_be_added(self):
        map = MapsFactory()

        ReportsFactory(
            ex_id=map.id,
            ex_name='maps'
        )

        user = UserFactory()

        response = self.post_authed(
            {
                'reportReason': 'reason 1',
                'infringement': 'true'
            },
            user,
            self._route.format(map.id)
        )

        reports = Reports.objects.all()

        self.assertEquals(
            2,
            reports.count()
        )

        new_report = Reports.objects.filter(user=user)[0]

        self.assertEquals(
            True,
            new_report.infringement
        )

        self.assertEquals(
            'reason 1',
            new_report.reason
        )

        map.refresh_from_db()

        self.assertEquals(
            2,
            map.amount_reports
        )

        self.assertEquals(
            302,
            response.status_code
        )

        self.assertEquals(
            '/maps/' + str(map.id),
            response.url
        )

    def test_a_report_will_not_be_added_if_one_already_exists_from_that_user(self):
        map = MapsFactory(
            amount_reports=1
        )

        user = UserFactory()

        ReportsFactory(
            user=user,
            ex_id=map.id,
            ex_name='maps',
            infringement=True
        )

        response = self.post_authed(
            {
                'reportReason': 'reason 1',
                'infringement': 'false'
            },
            user,
            self._route.format(map.id)
        )

        reports = Reports.objects.all()

        self.assertEquals(
            1,
            reports.count()
        )

        report = Reports.objects.filter()[0]

        self.assertEquals(
            True,
            report.infringement
        )

        self.assertNotEquals(
            'reason 1',
            report.reason
        )

        map.refresh_from_db()

        self.assertEquals(
            1,
            map.amount_reports
        )

        self.assertEquals(
            302,
            response.status_code
        )

        self.assertEquals(
            '/maps/' + str(map.id),
            response.url
        )
