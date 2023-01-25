from dependency_injector.wiring import Provide
from openra.classes.file_location import FileLocation
from openra.services.docker import Docker
from openra.services.utility.map_hash import MapHashCommand, MapHashTranslator
from openra.services.utility.map_rules_command import MapRulesCommand


class Utility:

    _docker: Docker

    def __init__(self,
                 docker: Docker = Provide['docker']
                 ) -> None:
        self._docker = docker

    def map_hash(self, engine_location: FileLocation, map_location: FileLocation):
        output = MapHashCommand(
            engine_location,
            map_location
        ).run_command(self._docker)

        return MapHashTranslator().translate(output)

    def map_rules(self, engine_location: FileLocation, map_location: FileLocation):
        return MapRulesCommand(
            engine_location,
            map_location
        ).run_command(self._docker)
