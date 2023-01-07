import datetime

from unittest import TestCase
from unittest.mock import  Mock, MagicMock
from fs.tempfs import TempFS
from openra.fakes import log
from openra.services.docker import Docker
from openra.services.utility import Utility
from openra.structs import FileLocation

class TestServiceUtility(TestCase):
    def test_map_hash_will_return_the_output_if_return_value_is_a_string(self):
        log.register()

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

        self.assertTrue(
            log.contains('info', 'Getting hash for map: ' + 'map.oramap')
        )
        self.assertTrue(
            log.contains('info', 'Map path: ' + map_location.get_os_dir())
        )
        self.assertTrue(
            log.contains('info', 'Success')
        )

    def test_map_hash_will_return_none_if_docker_returns_none(self):
        log.register()

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

        self.assertTrue(
            log.contains('info', 'Getting hash for map: ' + 'map.oramap')
        )
        self.assertTrue(
            log.contains('info', 'Map path: ' + map_location.get_os_dir())
        )
        self.assertTrue(
            log.contains('info', 'Failed')
        )
