from dependency_injector.wiring import Provide
from openra.facades import log
from openra.services.docker import Docker


class Utility:

    docker: Docker

    def __init__(self,
            docker:Docker=Provide['docker']
            ) -> None:
        self._docker = docker

    def map_hash(self, engine_path, map_location):
        map_file = map_location.file
        log().info('Getting hash for map: ' + map_file)

        map_path = map_location.get_os_dir()
        log().info('Map path: ' + map_path)

        result = self._docker.run_utility_command(
                engine_path,
                '--map-hash "/map/'+map_file+'"',
                '/map/:'+map_path
            )

        if result != None:
            log().info('Success')
        else:
            log().info('Failed')

        return result

