from dependency_injector.wiring import Provide, inject
from django.core.management.base import BaseCommand, CommandError
from openra.containers import Container
from openra.services.docker import Docker

class Command(BaseCommand):
    help = 'Checks that docker is functioning as needed'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        self.test_docker()

    @inject
    def test_docker(self, docker:Docker=Provide[Container.docker]):
        print(docker.test_docker())
