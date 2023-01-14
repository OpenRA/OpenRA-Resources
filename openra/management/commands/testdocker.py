from dependency_injector.wiring import Provide, inject
from django.core.management.base import BaseCommand
from openra.classes.exceptions import ExceptionBase
from openra.containers import Container
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
            print('Success:')
            print(docker.test_docker())
        except ExceptionBase as exception:
            print('Failed:')
            exception.print_full_details()
