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

    def runSeeder(self):
        call_command('seedtestdata', 'sampleuser@example.com', 'sampleuser', 'pass123')

    def mockFileSystem(self):
        container.dataFs.override(providers.Singleton(
            MemoryFS
        ))

    @inject
    def oramapFileExistsForMapId(self, mapId, dataFs:FS=Provide[Container.dataFs]):
        filePath = path.join('maps', str(mapId))
        if not dataFs.exists(filePath):
            return False

        for file in dataFs.scandir(filePath):
            if file.suffix == '.oramap':
                return True

        return False

    def test_it_creates_a_super_user_with_the_details_provided(self):
        self.mockFileSystem()
        self.runSeeder()

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
        self.mockFileSystem()

        self.assertFalse(self.oramapFileExistsForMapId(1))
        self.runSeeder()

        maps = Maps.objects.filter()

        standardMap = maps[0]

        self.assertIsNotNone(standardMap)

        self.assertEquals(
            'Sample Author',
            standardMap.author
        )

        self.assertTrue(self.oramapFileExistsForMapId(standardMap.id))

        yamlMap = maps[1]

        self.assertIsNotNone(yamlMap)

        self.assertEquals(
            'Sample YAML Map',
            yamlMap.author
        )

        self.assertTrue(self.oramapFileExistsForMapId(yamlMap.id))

        luaMap = maps[2]

        self.assertIsNotNone(luaMap)

        self.assertEquals(
            'Sample Lua Author',
            luaMap.author
        )

        self.assertTrue(self.oramapFileExistsForMapId(luaMap.id))
