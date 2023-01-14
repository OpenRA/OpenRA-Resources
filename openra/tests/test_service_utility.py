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
from openra.services.docker import Docker, ExceptionDockerNonByteResponse
from openra.services.log import Log
from openra.services.utility import Utility
from openra import container

class TestServiceUtility(TestCase):

    def test_map_hash_will_run_map_hash_with_docker_and_pass_on_output(self):
        overrides = container.override_providers(
            log = Singleton(FakeLog)
        )

        docker_mock = Mock(spec=Docker)
        docker_mock.run_utility_command = MagicMock(
            return_value = 'sample_hash'
        )
        utility = Utility(docker_mock)

        engine_location = FileLocation(
            TempFS(),
            '/engine/',
            ''
        )
        map_location = FileLocation(
            TempFS(),
            '/map/',
            'map.oramap'
        )

        map_hash = utility.map_hash(engine_location, map_location)

        docker_mock.run_utility_command.assert_called_once_with(
            engine_location.get_os_dir(),
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

        overrides.__exit__()
