import datetime

from django.utils import timezone
from django.test import TestCase
from django.core.management import call_command
from django.utils.six import StringIO
from django.contrib.auth import authenticate

from openra.models import User, Maps
from dependency_injector import providers
from dependency_injector.wiring import inject, Provide
from openra import container
from openra.containers import Container
from fs.memoryfs import MemoryFS
from fs.base import FS
from os import path

class TestCommandSeedTestData(TestCase):

    def run_seeder(self):
        call_command('seedtestdata', 'sampleuser@example.com', 'sampleuser', 'pass123')

    def mock_file_system(self):
        container.data_fs.override(providers.Singleton(
            MemoryFS
        ))

    @inject
    def oramap_file_exists_for_map_id(self, map_id, data_fs:FS=Provide[Container.data_fs]):
        file_path = path.join('maps', str(map_id))
        if not data_fs.exists(file_path):
            return False

        for file in data_fs.scandir(file_path):
            if file.suffix == '.oramap':
                return True

        return False

    def test_it_creates_a_super_user_with_the_details_provided(self):
        self.mock_file_system()
        self.run_seeder()

        user = User.objects.first()

        self.assertEqual(
            'sampleuser@example.com',
            user.email
        )

        self.assertEqual(
            'sampleuser',
            user.username
        )

        authed = authenticate(
            username='sampleuser',
            password='pass123'
        )

        self.assertEqual(authed, user)

        self.assertTrue(user.is_superuser)

        self.assertLess(
            user.date_joined,
            timezone.now()-timezone.timedelta(days=5)
        )

    def test_it_imports_the_sample_maps(self):
        self.mock_file_system()

        self.assertFalse(self.oramap_file_exists_for_map_id(1))
        self.run_seeder()

        maps = Maps.objects.filter()

        standard_map = maps[0]

        self.assertIsNotNone(standard_map)

        self.assertEquals(
            'Sample Author',
            standard_map.author
        )

        self.assertTrue(self.oramap_file_exists_for_map_id(standard_map.id))

        yaml_map = maps[1]

        self.assertIsNotNone(yaml_map)

        self.assertEquals(
            'Sample YAML Map',
            yaml_map.author
        )

        self.assertTrue(self.oramap_file_exists_for_map_id(yaml_map.id))

        lua_map = maps[2]

        self.assertIsNotNone(lua_map)

        self.assertEquals(
            'Sample Lua Author',
            lua_map.author
        )

        self.assertTrue(self.oramap_file_exists_for_map_id(lua_map.id))

class TestTestDocker(TestCase):

    def test_it_runs_the_test_docker_command(self):
        # Currently untestable but will be
        # once service injection gets merged
        pass
