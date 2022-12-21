import datetime

from django.utils import timezone
from django.test import TestCase
from django.core.management import call_command
from django.utils.six import StringIO
from django.contrib.auth import authenticate

from openra.models import User, Maps

class TestCommandSeedTestData(TestCase):

    def runSeeder(self):
        call_command('seedtestdata', 'sampleuser@example.com', 'sampleuser', 'pass123')

    def getSeededUser(self):
        return User.objects.first()

    def test_it_creates_a_super_user_with_the_details_provided(self):
        self.runSeeder()

        user = self.getSeededUser()

        self.assertEqual(
            'sampleuser@example.com',
            user.email
        )

        self.assertEqual(
            'sampleuser',
            user.username
        )

        authed = authenticate(
            username='sampleuser',
            password='pass123'
        )

        self.assertEqual(authed, user)

        self.assertTrue(user.is_superuser)

    def test_the_user_account_is_set_to_at_least_five_days_old(self):
        self.runSeeder()

        user = self.getSeededUser()

        self.assertLess(
            user.date_joined,
            timezone.now()-timezone.timedelta(days=5)
        )

    def test_it_imports_the_standard_map(self):

        self.runSeeder()

        standardMap = Maps.objects.first()

        self.assertIsNotNone(standardMap)

        self.assertEquals(
            'Sample Author',
            standardMap.author
        )


