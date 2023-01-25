

from dependency_injector.wiring import Provide
from openra.classes.file_location import FileLocation
from openra.services.docker import Docker
from openra.facades import log


class BaseMapCommand:

    _map_log_intro_message: str
    _utility_command: str

    engine_location: FileLocation
    map_location: FileLocation

    def __init__(self, engine_location: FileLocation, map_location: FileLocation):
        self.engine_location = engine_location
        self.map_location = map_location

    def run_command(self, docker: Docker):
        map_location = self.map_location
        engine_location = self.engine_location

        map_file = map_location.file
        log().info(self._map_log_intro_message + map_file)

        map_path = map_location.get_os_dir()
        log().info('Map path: ' + map_path)

        result = docker.run_utility_command(
            engine_location.get_os_dir(),
            self._utility_command + ' "/map/' + map_file + '"',
            [map_path + ':/map/']
        )

        log().info('Success')

        return result
