from unittest.mock import Mock
from dependency_injector.providers import Singleton
from dependency_injector.wiring import providers

from django.core.management import call_command
from django.test.testcases import TestCase

from openra import container
from openra.fakes.engine_file_repository import FakeEngineFileRepository
from openra.fakes.log import FakeLog
from openra.fakes.file_downloader import FakeFileDownloader
from openra.fakes.github import FakeGithub
from openra.models import Engines
from openra.services.file_downloader import FileDownloader

class TestImportLatestEngines(TestCase):
    def test_command_will_import_engines(self):
        overrides = container.override_providers(
            log = Singleton(FakeLog),
            github = Singleton(FakeGithub),
            engine_file_repository = Singleton(FakeEngineFileRepository),
            file_downloader = Singleton(FakeFileDownloader)
        )

        self.assertEquals(
            0,
            Engines.objects.count()
        )

        call_command('import_latest_engines')

        self.assertEquals(
            6,
            Engines.objects.count()
        )

        expected_engines = [{
            'mod': 'ra',
            'version': 'playtest-7'
        },{
            'mod': 'td',
            'version': 'playtest-7'
        },{
            'mod': 'd2k',
            'version': 'playtest-7'
        },{
            'mod': 'ra',
            'version': 'release-5'
        },{
            'mod': 'td',
            'version': 'release-5'
        },{
            'mod': 'd2k',
            'version': 'release-5'
        }]

        self.assertEqual(
            expected_engines,
            container.engine_file_repository().imported
        )

        for engine in expected_engines:
            self.assertTrue(
                Engines.objects.filter(
                    game_mod=engine['mod'],
                    version=engine['version']
                ).exists()
        )

        overrides.__exit__()

    def test_command_arg_can_be_set_to_number_of_releases_back(self):
        overrides = container.override_providers(
            log = Singleton(FakeLog),
            github = Singleton(FakeGithub),
            engine_file_repository = Singleton(FakeEngineFileRepository),
            file_downloader = Singleton(FakeFileDownloader)
        )

        container.github().only_ra_asset = True

        call_command('import_latest_engines', '2')

        expected_engines = [{
            'mod': 'ra',
            'version': 'playtest-7'
        },{
            'mod': 'ra',
            'version': 'release-5'
        },{
            'mod': 'ra',
            'version': 'release-3'
        }]

        self.assertEquals(
            3,
            len(container.file_downloader().downloaded)
        )

        self.assertEqual(
            expected_engines,
            container.engine_file_repository().imported
        )

        for engine in expected_engines:
            self.assertTrue(
                Engines.objects.filter(
                    game_mod=engine['mod'],
                    version=engine['version']
                ).exists()
        )

        overrides.__exit__()

    def test_command_will_not_download_appimage_if_they_exist(self):
        overrides = container.override_providers(
            log = Singleton(FakeLog),
            github = Singleton(FakeGithub),
            engine_file_repository = Singleton(FakeEngineFileRepository),
            file_downloader = Singleton(FakeFileDownloader)
        )

        container.github().only_one_release = True
        container.github().only_ra_asset = True
        container.engine_file_repository().engine_exists = True

        call_command('import_latest_engines')

        self.assertEquals(
            0,
            len(container.file_downloader().downloaded)
        )

        expected_engines = [{
            'mod': 'ra',
            'version': 'release-5'
        }]

        self.assertEqual(
            [],
            container.engine_file_repository().imported
        )

        for engine in expected_engines:
            self.assertTrue(
                Engines.objects.filter(
                    game_mod=engine['mod'],
                    version=engine['version']
                ).exists()
        )

        overrides.__exit__()

    def test_command_will_not_create_models_if_they_already_exist(self):
        overrides = container.override_providers(
            log = Singleton(FakeLog),
            github = Singleton(FakeGithub),
            engine_file_repository = Singleton(FakeEngineFileRepository),
            file_downloader = Singleton(FakeFileDownloader)
        )

        container.github().only_one_release = True
        container.github().only_ra_asset = True

        engine = Engines(
            game_mod='ra',
            version='release-5'
        )
        engine.save()

        self.assertEquals(
            1,
            Engines.objects.count()
        )

        call_command('import_latest_engines')

        self.assertEquals(
            1,
            Engines.objects.count()
        )

        expected_engines = [{
            'mod': 'ra',
            'version': 'release-5'
        }]

        self.assertEqual(
            expected_engines,
            container.engine_file_repository().imported
        )

        for engine in expected_engines:
            self.assertTrue(
                Engines.objects.filter(
                    game_mod=engine['mod'],
                    version=engine['version']
                ).exists()
        )

        overrides.__exit__()
