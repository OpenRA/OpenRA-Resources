from django.conf import os
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings
import factory
from fs.memoryfs import MemoryFS
from registration.forms import User

from openra import content
from openra.containers import Container, container
from openra.models import Reports, Screenshots
from openra.tests.factories import MapsFactory, ReportsFactory, ScreenshotsFactory, UserFactory
from openra.tests.routes.test_route_base import TestRouteBase


class TestRouteMapsUpdateMapInfo(TestRouteBase):

    _route = '/maps/{}/upload-screenshot'

    def __get_uploaded_image_file(self):
        with open('openra/static/images/soviet-logo-fallback.png', 'rb') as file:
            data = file.read()
        return SimpleUploadedFile(
            'image.jpg',
            data,
            content_type='image/png'
        )

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

    def test_a_screenshot_can_be_added_by_the_map_uploader(self):
        data_fs = MemoryFS()

        container.reset_singletons()
        overrides = container.override_providers(
            data_fs=data_fs
        )
        user = UserFactory()

        map = MapsFactory(
            user=user
        )

        response = self.post_authed(
            {
                'screenshot': self.__get_uploaded_image_file()
            },
            user,
            self._route.format(map.id)
        )

        map.refresh_from_db()

        screenshots = Screenshots.objects.filter(
            ex_name='maps',
            ex_id=map.id
        )

        self.assertEquals(
            1,
            screenshots.count()
        )

        screenshot = screenshots[0]

        self.assertTrue(
            data_fs.exists(
                os.path.join('screenshots', str(screenshot.id), str(map.id) + '.png')
            )
        )

        self.assertTrue(
            data_fs.exists(
                os.path.join('screenshots', str(screenshot.id), str(map.id) + '-mini.png')
            )
        )

        self.assertEquals(
            302,
            response.status_code
        )

        self.assertEquals(
            '/maps/' + str(map.id),
            response.url
        )

        overrides.__exit__()

    def test_screenshots_can_be_added_by_a_superuser(self):
        data_fs = MemoryFS()

        container.reset_singletons()
        overrides = container.override_providers(
            data_fs=data_fs
        )

        user = UserFactory(
            is_superuser=True
        )

        map = MapsFactory()

        response = self.post_authed(
            {
                'screenshot': self.__get_uploaded_image_file()
            },
            user,
            self._route.format(map.id)
        )

        map.refresh_from_db()

        screenshots = Screenshots.objects.filter(
            ex_name='maps',
            ex_id=map.id
        )

        self.assertEquals(
            1,
            screenshots.count()
        )

        screenshot = screenshots[0]

        self.assertTrue(
            data_fs.exists(
                os.path.join('screenshots', str(screenshot.id), str(map.id) + '.png')
            )
        )

        self.assertTrue(
            data_fs.exists(
                os.path.join('screenshots', str(screenshot.id), str(map.id) + '-mini.png')
            )
        )

        self.assertEquals(
            302,
            response.status_code
        )

        self.assertEquals(
            '/maps/' + str(map.id),
            response.url
        )

        overrides.__exit__()

    def test_screenshots_cannot_be_added_by_other_users(self):
        user = UserFactory()

        map = MapsFactory()

        response = self.post_authed(
            {
                'screenshot': self.__get_uploaded_image_file()
            },
            user,
            self._route.format(map.id)
        )

        map.refresh_from_db()

        self.assertEquals(
            0,
            Screenshots.objects.count()
        )

        self.assertEquals(
            302,
            response.status_code
        )

        self.assertEquals(
            '/maps/' + str(map.id),
            response.url
        )
