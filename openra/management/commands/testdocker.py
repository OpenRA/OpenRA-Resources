from django.core.management.base import BaseCommand, CommandError
from openra.services.docker import Docker

class Command(BaseCommand):
    help = 'Checks that docker is functioning as needed'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        print(Docker().testDocker())
