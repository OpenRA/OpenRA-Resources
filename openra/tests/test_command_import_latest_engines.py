from unittest import TestCase
from dependency_injector.providers import Singleton
from dependency_injector.wiring import providers

from django.core.management import call_command

from openra import container
from openra.fakes.engine_file_repository import FakeEngineFileRepository
from openra.fakes.log import FakeLog
from openra.fakes.file_downloader import FakeFileDownloader
from openra.fakes.github import FakeGithub

class TestImportLatestEngines(TestCase):
    def test_command_will_import_engines(self):
        overrides = container.override_providers(
            log = Singleton(FakeLog),
            github = Singleton(FakeGithub),
            engine_file_repository = Singleton(FakeEngineFileRepository),
            file_downloader = Singleton(FakeFileDownloader)
        )

        call_command('import_latest_engines')

        self.assertEqual([
            {
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

            }],
            container.engine_file_repository().imported
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

        self.assertEqual([
            {
                'mod': 'ra',
                'version': 'playtest-7'
            },{
                'mod': 'ra',
                'version': 'release-5'
            },{
                'mod': 'ra',
                'version': 'release-3'
            }],
            container.engine_file_repository().imported
        )

        overrides.__exit__()
