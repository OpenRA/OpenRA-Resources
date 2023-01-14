import factory

from openra import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserFactory(factory.Factory):

    class Meta:
        model = User

    username = factory.Faker('first_name')
    password = 'password'
    email = factory.Faker('email')
    date_joined = timezone.now()
    is_superuser = False

class MapsFactory(factory.Factory):

    class Meta:
        model = models.Maps

    user = factory.SubFactory(UserFactory)
    title = factory.Faker('word')
    description = factory.Faker('paragraph')
    info = factory.Faker('paragraph')
    author = factory.Faker('word')
    map_type = 'conquest'
    categories = factory.Faker('word')
    players = factory.Faker('random_number')
    game_mod = 'RA'
    map_hash = factory.Faker('random_letters')
    width = factory.Faker('word')
    height = factory.Faker('word')
    bounds = factory.Faker('word')
    tileset = factory.Faker('word')
    spawnpoints = factory.Faker('paragraph')
    mapformat = factory.Faker('random_number')
    parser = factory.Faker('word')
    shellmap = False
    base64_rules = factory.Faker('paragraph')
    base64_players = factory.Faker('paragraph')
    legacy_map = False
    revision = 1
    pre_rev = 0
    next_rev = 0
    downloading = True
    requires_upgrade = False
    advanced_map = False
    lua = False
    posted = timezone.now()
    viewed = 0
    downloaded = 0
    rating = 0.0
    amount_reports = 0
    policy_cc = False
    policy_adaptations = factory.Faker('word')
    policy_commercial = False

class MapCategoriesFactory(factory.Factory):

    class Meta:
        model = models.MapCategories

    category_name = factory.Faker('word')
    posted = timezone.now()

class MapUpgradeLogsFactory(factory.Factory):

    class Meta:
        model = models.MapUpgradeLogs

    map_id = factory.SubFactory(MapsFactory)
    date_run = timezone.now()
    from_version = factory.Faker('word')
    to_version = factory.Faker('word')
    upgrade_output = factory.Faker('paragraph')

class LintsFactory(factory.Factory):

    class Meta:
        model = models.Lints

    item_type = "maps"
    map_id = factory.SubFactory(MapsFactory)
    version_tag = factory.Faker('word')
    pass_status = True
    lint_output = factory.Faker('paragraph')
    posted = timezone.now()

class CommentsFactory(factory.Factory):

    class Meta:
        model = models.Comments

    user = factory.SubFactory(UserFactory)
    content = factory.Faker('paragraph')
    item_type = "maps"
    item_id = factory.SubFactory(MapsFactory)
    posted = timezone.now()
    is_removed = False

class UnsubscribeCommentsFactory(factory.Factory):

    class Meta:
        model = models.UnsubscribeComments

    user = factory.SubFactory(UserFactory)
    item_type = "maps"
    item_id = factory.SubFactory(MapsFactory)
    unsubscribed = timezone.now()

class ReportsFactory(factory.Factory):

    class Meta:
        model = models.Reports

    user = factory.SubFactory(UserFactory)
    reason = factory.Faker('paragraph')
    ex_id = 0
    ex_name = ''
    infringement = False
    posted = timezone.now()

class ScreenshotsFactory(factory.Factory):

    class Meta:
        model = models.Screenshots

    user = factory.SubFactory(UserFactory)
    ex_id = 0
    ex_name = ''
    posted = timezone.now()
    map_preview = False

class RatingFactory(factory.Factory):

    class Meta:
        model = models.Rating

    user = factory.SubFactory(UserFactory)
    ex_id = 0
    ex_name = ''
    rating = 0.0
    posted = timezone.now()

class EngineFactory(factory.Factory):

    class Meta:
        model = models.Maps

    game_mod = 'RA'
    parser = factory.Faker('word')
