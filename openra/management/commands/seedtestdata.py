from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.utils import timezone

from openra.models import Maps

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

        map = Maps.objects.create(
            user                = user,
            title               = 'Sample Standard Map',
            description         = 'Description of Sample Standard Map',
            info                = 'Info for Sample Standard Map',
            author              = 'Sample Author',
            map_type            = 'Sample Type',
            categories          = 'Sample Category, Sample Category 2',
            players             = 2,
            game_mod            = 'Red Alert',
            map_hash            = 'unknown',
            width               = '16',
            height              = '16',
            bounds              = '',
            tileset             = 'snow',
            spawnpoints         = '',
            mapformat           = '342',
            parser              = 'release-20141029',
            shellmap            = False,
            base64_rules        = 'super long rules',
            base64_players      = 'super long players',
            legacy_map          = False,
            revision            = 1,
            pre_rev             = 0,
            next_rev            = 0,
            downloading         = True,
            requires_upgrade    = False,
            advanced_map        = False,
            lua                 = False,
            posted              = '2022-12-01',
            viewed              = 0,
            downloaded          = 0,
            rating              = 0.0,
            amount_reports      = 0,
            policy_cc           = False,
            policy_adaptations  = True,
            policy_commercial   = False
        )

        self.stdout.write('Database seeded')

