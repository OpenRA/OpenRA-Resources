from dependency_injector.wiring import Provide, inject
from django.core.management.base import BaseCommand
from openra.classes.exceptions import ExceptionBase
from openra.classes.release import Release
from openra.containers import Container
from openra.facades import log
from openra.models import Engines, Maps
from openra.services.docker import Docker
from openra.services.engine_file_repository import EngineFileRepository
from openra.services.map_file_repository import MapFileRepository
from openra.services.utility import Utility


class Command(BaseCommand):
    help = 'Test utility commands against an engine for expected output'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        self._handle()

    @inject
    def _handle(self,
                utility: Utility = Provide[Container.utility],
                engine_file_repository: EngineFileRepository = Provide[Container.engine_file_repository],
                map_file_repository: MapFileRepository = Provide[Container.map_file_repository]):

        try:
            engine_model = Engines.objects.latest('id')
            map_model = Maps.objects.latest('id')

            release = Release(engine_model.game_mod, engine_model.version)

            engine_location = engine_file_repository.get_path(release)
            map_location = map_file_repository.get_oramap_path(map_model.id)

            map_hash = utility.map_hash(engine_location, map_location)
            log().info('Map hash: ' + map_hash.map_hash)

            map_rules = utility.map_rules(engine_location, map_location)
            log().info('Map rules: ' + map_rules)
        except ExceptionBase as exception:
            log().exception_obj(exception)
