from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.files import File

from openra.handlers import process_upload

class Command(BaseCommand):
    help = 'Seeds the database with some test data'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str)
        parser.add_argument('username', type=str)
        parser.add_argument('password', type=str)

    def handle(self, *args, **options):
        email = options['email']
        username = options['username']
        password = options['password']

        user = User.objects.create_superuser(
            username=username,
            password=password,
            email=email,
            date_joined=timezone.now()-timezone.timedelta(days=6)
        )

        process_upload(
            user.id,
            File(open('openra/resources/sample-maps/sample-standard-map.oramap', 'rb')),
            {
                'policy_cc': 'yes',
                'name': 'Sample Map',
                'info': 'Info about sample map'
            }
        )

        process_upload(
            user.id,
            File(open('openra/resources/sample-maps/sample-yaml-map.oramap', 'rb')),
            {
                'policy_cc': 'yes',
                'name': 'Sample YAML Map',
                'info': 'Info about sample YAML map'
            }
        )

        process_upload(
            user.id,
            File(open('openra/resources/sample-maps/sample-lua-map.oramap', 'rb')),
            {
                'policy_cc': 'no',
                'name': 'Sample Lua Map',
                'info': 'Info about sample Lua map'
            }
        )

        self.stdout.write('Database seeded')

