

from dependency_injector.wiring import Provide
from openra.classes.file_location import FileLocation
from openra.classes.map_hash import MapHash
from openra.services.docker import Docker
from openra.facades import log
from openra.services.utility.base_map_command import BaseMapCommand
from openra.services.utility.exceptions import ExceptionUtilityMapHashUnableToTranslate
import re

class MapHashCommand(BaseMapCommand):

    _map_log_intro_message:str = "Getting hash for map: "
    _utility_command:str = "--map-hash"

class MapHashTranslator:

    def translate(self, output:str):
        if not re.match("^[A-z0-9]{40}$", output):
            raise ExceptionUtilityMapHashUnableToTranslate(
                output
            )
        return MapHash(output)

