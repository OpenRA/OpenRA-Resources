from dependency_injector.wiring import Provide, inject
from django.core.management.base import BaseCommand
from openra.classes.exceptions import ExceptionBase
from openra.containers import Container
from openra.facades import log
from openra.services.docker import Docker

class Command(BaseCommand):
    help = 'Checks that docker is functioning as needed'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        self._test_docker()

    @inject
    def _test_docker(self, docker:Docker=Provide[Container.docker]):
        try:
            log().info(docker.test_docker())
        except ExceptionBase as exception:
            log().exception_obj(exception)
