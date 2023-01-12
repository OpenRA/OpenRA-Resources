from unittest import TestCase

from django.core.management import call_command

from openra import container
from openra.fakes.log import FakeLog
from openra.fakes.engine_provider import FakeEngineProvider
from openra.fakes.file_downloader import FakeFileDownloader
from openra.fakes.github import FakeGithub

class TestImportLatestEngines(TestCase):
    def test_it_will_import_engines(self):
        fake_log = FakeLog()
        fake_github = FakeGithub()
        fake_engine_provider = FakeEngineProvider()
        fake_file_downloader = FakeFileDownloader()
        container.log.override(
            fake_log
        )
        container.github.override(
            fake_github
        )
        container.engine_provider.reset_override()
        container.engine_provider.override(
            fake_engine_provider
        )
        container.file_downloader.override(
            fake_file_downloader
        )
        call_command('import_latest_engines')

        self.assertEqual([
            {
                'mod': 'ra',
                'version': 'playtest-6'
            },{
                'mod': 'td',
                'version': 'playtest-6'
            },{
                'mod': 'd2k',
                'version': 'playtest-6'
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
            fake_engine_provider.imported
        )

    def test_it_can_be_set_to_import_up_to_x_releases_back_skipping_in_between_playtests(self):
        fake_log = FakeLog()
        fake_github = FakeGithub()
        fake_github.only_ra_asset = True
        fake_engine_provider = FakeEngineProvider()
        fake_file_downloader = FakeFileDownloader()
        container.log.override(
            fake_log
        )
        container.github.override(
            fake_github
        )
        container.engine_provider.override(
            fake_engine_provider
        )
        container.file_downloader.override(
            fake_file_downloader
        )
        call_command('import_latest_engines', '2')

        self.assertEqual([
            {
                'mod': 'ra',
                'version': 'playtest-6'
            },{
                'mod': 'ra',
                'version': 'release-5'
            },{
                'mod': 'ra',
                'version': 'release-3'
            }],
            fake_engine_provider.imported
        )
