

from dependency_injector.wiring import Provide
from openra.classes.file_location import FileLocation
from openra.services.docker import Docker
from openra.facades import log
from openra.services.utility.base_map_command import BaseMapCommand


class MapRulesCommand(BaseMapCommand):

    _map_log_intro_message: str = "Getting rules for map: "
    _utility_command: str = "--map-rules"
