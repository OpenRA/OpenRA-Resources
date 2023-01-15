
from unittest import TestCase
from unittest.mock import MagicMock, Mock
from dependency_injector.providers import Provider, Singleton

from django.core.management import call_command
from openra import container
from openra.classes.map_hash import MapHash
from openra.fakes.engine_file_repository import FakeEngineFileRepository
from openra.fakes.file_downloader import FakeFileDownloader
from openra.fakes.map_file_repository import FakeMapFileRepository
from openra.fakes.log import FakeLog
from openra.services.utility import Utility

from openra.tests.factories import EngineFactory, MapsFactory


class TestTestUtility(TestCase):

    def test_test_utility_runs_each_of_the_utility_command_and_prints_the_response(self):
        overrides = container.override_providers(
            engine_file_repository = Singleton(FakeEngineFileRepository),
            map_file_repository = Singleton(FakeMapFileRepository),
            log = Singleton(FakeLog),
        )

        container.engine_file_repository().engine_exists = True

        utility_mock = Mock(spec=Utility)
        utility_mock.map_hash = MagicMock(
            return_value = MapHash("sample_hash")
        )
        utility_mock.map_rules = MagicMock(
            return_value = 'map rules'
        )
        container.utility.override(
            utility_mock
        )

        engine = EngineFactory()
        engine.save()
        map = MapsFactory(
            game_mod = engine.game_mod
        )
        map.save()

        call_command('test_utility')


        utility_mock.map_hash.assert_called_once()
        utility_mock.map_rules.assert_called_once()

        overrides.__exit__()

