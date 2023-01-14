import datetime

from django.utils import timezone
from django.test import TestCase

from . import factories

class TestFactories(TestCase):

    def test_it_can_create_models_from_all_factories(self):
        factories.UserFactory()
        factories.MapsFactory()
        factories.MapCategoriesFactory()
        factories.MapUpgradeLogsFactory()
        factories.LintsFactory()
        factories.CommentsFactory()
        factories.UnsubscribeCommentsFactory()
        factories.ReportsFactory()
        factories.ScreenshotsFactory()
        factories.RatingFactory()
        factories.EngineFactory()
