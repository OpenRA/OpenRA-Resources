import datetime
from logging import log

from unittest import TestCase
from unittest.mock import  Mock, MagicMock
from dependency_injector.providers import Singleton
from dependency_injector.wiring import Provider, providers
from fs.tempfs import TempFS
from openra.classes.file_location import FileLocation
from openra.containers import Container
from openra.fakes.log import FakeLog
from openra.services.docker import Docker
from openra.services.log import Log
from openra.services.utility import Utility
from openra import container

class TestServiceUtility(TestCase):
    def test_map_hash_will_return_the_output_if_return_value_is_a_string(self):
        with container.override_providers(
            log = Singleton(FakeLog)
        ):

            docker_mock = Mock(spec=Docker)
            docker_mock.run_utility_command = MagicMock(
                return_value = 'sample_hash'
            )
            utility = Utility(docker_mock)

            engine_path = '/engine/'
            map_location = FileLocation(
                TempFS(),
                '/map/',
                'map.oramap'
            )

            map_hash = utility.map_hash(engine_path, map_location)

            docker_mock.run_utility_command.assert_called_once_with(
                engine_path,
                '--map-hash "/map/' + map_location.file + '"',
                '/map/:' + map_location.get_os_dir()
            )

            self.assertEquals(
                'sample_hash',
                map_hash
            )


            log = container.log()

            self.assertTrue(
                log.contains('info', 'Getting hash for map: map.oramap')
            )

            self.assertTrue(
                log.contains('info', 'Map path: ' + map_location.get_os_dir())
            )

            self.assertTrue(
                log.contains('info', 'Success')
            )

    def test_map_hash_will_return_none_if_docker_returns_none(self):
        overrides = container.override_providers(
            log = Singleton(FakeLog)
        )

        docker_mock = Mock(spec=Docker)
        docker_mock.run_utility_command = MagicMock(
            return_value = None
        )
        utility = Utility(docker_mock)

        engine_path = '/engine/'
        map_location = FileLocation(
            TempFS(),
            '/map/',
            'map.oramap'
        )

        result = utility.map_hash(engine_path, map_location)

        docker_mock.run_utility_command.assert_called_once_with(
            engine_path,
            '--map-hash "/map/' + map_location.file + '"',
            '/map/:' + map_location.get_os_dir()
        )

        self.assertEquals(
            None,
            result
        )

        log = container.log()

        self.assertTrue(
            log.contains('info', 'Getting hash for map: ' + 'map.oramap')
        )
        self.assertTrue(
            log.contains('info', 'Map path: ' + map_location.get_os_dir())
        )
        self.assertTrue(
            log.contains('info', 'Failed')
        )

        overrides.__exit__()
