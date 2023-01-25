import datetime

from django.utils import timezone
from django.test import TestCase

from . import factories


class TestFactories(TestCase):

    def test_it_can_create_saveable_models_from_all_factories(self):
        factories.UserFactory().save()
        factories.MapsFactory().save()
        factories.MapCategoriesFactory().save()
        factories.MapUpgradeLogsFactory().save()
        factories.LintsFactory().save()
        factories.CommentsFactory().save()
        factories.UnsubscribeCommentsFactory().save()
        factories.ReportsFactory().save()
        factories.ScreenshotsFactory().save()
        factories.RatingFactory().save()
        factories.EngineFactory().save()
