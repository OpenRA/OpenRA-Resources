

from django.test import override_settings
from dependency_injector.providers import Singleton
from fs.base import FS
from fs.memoryfs import MemoryFS
from openra.classes.file_location import FileLocation
from openra.fakes.map_file_repository import FakeMapFileRepository
from openra.tests.factories import MapsFactory
from openra.tests.routes.test_route_base import TestRouteBase
from openra.containers import container


class TestRouteDisplayMap(TestRouteBase):

    _route = '/maps/{}'

    def test_route_can_be_accessed_by_any_user(self):
        overrides = container.override_providers(
            map_file_repository=Singleton(FakeMapFileRepository)
        )

        data_fs = MemoryFS()

        container.map_file_repository().lua_paths = [
            FileLocation(
                data_fs,
                'test',
                'sample_lua_name.lua'
            )
        ]

        FakeMapFileRepository.map_exists = False

        model = MapsFactory(lua=True)
        model.lua = True

        response = self.get(
            {},
            self._route.format(model.id),
        )

        self.assertEquals(
            200,
            response.status_code
        )

        self.assert_contains(
            response,
            [
                str(model.title),
                'sample_lua_name',
            ],
        )

        overrides.__exit__()

    @override_settings(SITE_MAINTENANCE=True)
    def test_route_shows_maintenance_page(self):
        model = MapsFactory()
        self.assert_is_maintenance(
            self.get(
                route=self._route.format(model.id),
            )
        )

    def test_redirects_to_homepage_if_map_not_foud(self):

        response = self.get(
            route=self._route.format(1234),
        )

        self.assertRedirects(response, '/')

    def test_redirects_to_homepage_if_map_files_not_found(self):

        model = MapsFactory()
        response = self.get(
            {},
            self._route.format(model.id),
        )

        self.assertRedirects(response, '/')
