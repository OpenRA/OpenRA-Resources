import datetime
from logging import log

from unittest import TestCase
from unittest.mock import  Mock, MagicMock
from dependency_injector.providers import Singleton
from dependency_injector.wiring import Provider, providers
from fs.tempfs import TempFS
from openra.classes.file_location import FileLocation
from openra.classes.map_hash import MapHash
from openra.containers import Container
from openra.fakes.log import FakeLog
from openra.services.docker import Docker, ExceptionDockerNonByteResponse
from openra.services.log import Log
from openra.services.utility import Utility
from openra.containers import container
from openra.services.utility.exceptions import ExceptionUtilityMapHashUnableToTranslate

class TestServiceUtility(TestCase):

    def _create_docker_mock(self, output:str):
        docker_mock = Mock(spec=Docker)
        docker_mock.run_utility_command = MagicMock(
            return_value = output
        )
        return docker_mock

    def _create_fake_engine_location(self):
        return FileLocation(
            TempFS(),
            '/engine/',
            ''
        )

    def _create_fake_map_location(self):
        return FileLocation(
            TempFS(),
            '/map/',
            'map.oramap'
        )

    def test_map_hash_runs_command_and_returns_map_hash(self):
        overrides = container.override_providers(
            log = Singleton(FakeLog)
        )

        sample_hash = ''.rjust(40, 'A')

        docker_mock = self._create_docker_mock(
            sample_hash
        )
        utility = Utility(docker=docker_mock)

        engine_location = self._create_fake_engine_location()
        map_location = self._create_fake_map_location()

        map_hash = utility.map_hash(engine_location, map_location)

        docker_mock.run_utility_command.assert_called_once_with(
            engine_location.get_os_dir(),
            '--map-hash "/map/' + map_location.file + '"',
            [map_location.get_os_dir()+':/map/']
        )

        self.assertIsInstance(
            map_hash,
            MapHash
        )

        self.assertEquals(
            sample_hash,
            map_hash.map_hash
        )

        self.assertTrue(
            container.log().contains_all([
                ['info', 'Getting hash for map: map.oramap'],
                ['info', 'Map path: ' + map_location.get_os_dir()],
                ['info', 'Success'],
            ])
        )

        overrides.__exit__()

    def test_map_hash_throws_an_exception_with_incorrect_output(self):
        overrides = container.override_providers(
            log = Singleton(FakeLog)
        )

        docker_mock = self._create_docker_mock(
            'line 1\nline 2'
        )
        utility = Utility(docker=docker_mock)

        engine_location = self._create_fake_engine_location()
        map_location = self._create_fake_map_location()

        self.assertRaises(
            ExceptionUtilityMapHashUnableToTranslate,
            utility.map_hash,
            engine_location,
            map_location
        )


        docker_mock.run_utility_command.assert_called_once_with(
            engine_location.get_os_dir(),
            '--map-hash "/map/' + map_location.file + '"',
            [map_location.get_os_dir()+':/map/']
        )

        self.assertTrue(
            container.log().contains_all([
                ['info', 'Getting hash for map: map.oramap'],
                ['info', 'Map path: ' + map_location.get_os_dir()]
            ])
        )

        overrides.__exit__()

## TODO Improve this to parse the rules
    def test_map_rules_runs_with_docker_and_pass_on_output(self):
        overrides = container.override_providers(
            log = Singleton(FakeLog)
        )

        docker_mock = self._create_docker_mock(
            'sample_rules'
        )
        utility = Utility(docker=docker_mock)

        engine_location = self._create_fake_engine_location()
        map_location = self._create_fake_map_location()

        map_rules = utility.map_rules(engine_location, map_location)

        docker_mock.run_utility_command.assert_called_once_with(
            engine_location.get_os_dir(),
            '--map-rules "/map/' + map_location.file + '"',
            [map_location.get_os_dir()+':/map/']
        )

        self.assertEquals(
            'sample_rules',
            map_rules
        )

        self.assertTrue(
            container.log().contains_all([
                ['info', 'Getting rules for map: map.oramap'],
                ['info', 'Map path: ' + map_location.get_os_dir()],
                ['info', 'Success'],
            ])
        )

        overrides.__exit__()
