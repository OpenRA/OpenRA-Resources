from django.db import models
from django.contrib.auth.models import User
from djangoratings.fields import RatingField

class UserOptions(models.Model):

    class Meta:
        verbose_name = 'UserOption'

    user                = models.ForeignKey(User)
    notifications_email = models.BooleanField(default=False)
    notifications_site  = models.BooleanField(default=True)

class Maps(models.Model):
    
    class Meta:
        verbose_name = 'Map'

    user                = models.ForeignKey(User)
    title               = models.CharField(max_length=200)
    description         = models.CharField(max_length=2000)
    info                = models.CharField(max_length=2000)
    author              = models.CharField(max_length=60)
    map_type            = models.CharField(max_length=40)
    players             = models.IntegerField(default=0)
    game_mod            = models.CharField(max_length=16)
    map_hash            = models.CharField(max_length=40)
    width               = models.CharField(max_length=16)
    height              = models.CharField(max_length=16)
    tileset             = models.CharField(max_length=16)
    revision            = models.IntegerField(default=1)
    pre_rev             = models.IntegerField(default=0)
    next_rev            = models.IntegerField(default=0)
    downloading         = models.BooleanField(default=True)
    requires_upgrade    = models.BooleanField(default=False)
    advanced_map        = models.BooleanField(default=False)
    lua                 = models.BooleanField(default=False)
    posted              = models.DateTimeField('date published')
    viewed              = models.IntegerField(default=0)
    downloaded          = models.IntegerField(default=0)
    rating              = RatingField(range=5, allow_anonymous=True, use_cookies=True)
    policy_cc           = models.BooleanField(default=False)
    policy_adaptations  = models.CharField(max_length=30)
    policy_commercial   = models.BooleanField(default=False)

class Units(models.Model):

    class Meta:
        verbose_name = 'Unit'

    user                = models.ForeignKey(User)
    title               = models.CharField(max_length=200)
    info                = models.CharField(max_length=2000)
    unit_type           = models.CharField(max_length=16)
    category            = models.CharField(max_length=16)
    palette             = models.CharField(max_length=16)
    revision            = models.IntegerField(default=1)
    pre_rev             = models.IntegerField(default=0)
    next_rev            = models.IntegerField(default=0)
    posted              = models.DateTimeField('date published')
    viewed              = models.IntegerField(default=0)
    downloaded          = models.IntegerField(default=0)
    rating              = RatingField(range=5, allow_anonymous=True, use_cookies=True)
    policy_cc           = models.BooleanField(default=False)
    policy_adaptations  = models.CharField(max_length=30)
    policy_commercial   = models.BooleanField(default=False)

class Mods(models.Model):

    class Meta:
        verbose_name = 'Mod'

    user                = models.ForeignKey(User)
    title               = models.CharField(max_length=200)
    info                = models.CharField(max_length=2000)
    revision            = models.IntegerField(default=1)
    pre_rev             = models.IntegerField(default=0)
    next_rev            = models.IntegerField(default=0)
    posted              = models.DateTimeField('date published')
    viewed              = models.IntegerField(default=0)
    downloaded          = models.IntegerField(default=0)
    rating              = RatingField(range=5, allow_anonymous=True, use_cookies=True)
    policy_cc           = models.BooleanField(default=False)
    policy_adaptations  = models.CharField(max_length=30)
    policy_commercial   = models.BooleanField(default=False)

class Replays(models.Model):

    class Meta:
        verbose_name = 'Replay'

    user                = models.ForeignKey(User)
    title               = models.CharField(max_length=200)
    info                = models.CharField(max_length=2000)
    version             = models.CharField(max_length=50)
    posted              = models.DateTimeField('date published')
    viewed              = models.IntegerField(default=0)
    downloaded          = models.IntegerField(default=0)

class Palettes(models.Model):

    class Meta:
        verbose_name = 'Palette'

    user                = models.ForeignKey(User)
    title               = models.CharField(max_length=200)
    info                = models.CharField(max_length=2000)
    used                = models.IntegerField(default=0)
    posted              = models.DateTimeField('date published')

class Reports(models.Model):

    class Meta:
        verbose_name = 'Report'

    user                = models.ForeignKey(User)
    reason              = models.CharField(max_length=2000)
    ex_id               = models.IntegerField(default=0)
    ex_name             = models.CharField(max_length=16)
    infringement        = models.BooleanField(default=False)
    posted              = models.DateTimeField('date published')

class Comments(models.Model):

    class Meta:
        verbose_name = 'Comment'

    user                = models.ForeignKey(User)
    message             = models.CharField(max_length=400)
    ex_id               = models.IntegerField(default=0)
    ex_name             = models.CharField(max_length=16)
    posted              = models.DateTimeField('date published')

class Screenshots(models.Model):

    class Meta:
        verbose_name = 'Screenshot'

    user                = models.ForeignKey(User)
    ex_id               = models.IntegerField(default=0)
    ex_name             = models.CharField(max_length=16)
    posted              = models.DateTimeField('date published')
    map_preview         = models.BooleanField(default=False)

class CrashReports(models.Model):

    class Meta:
        verbose_name = 'CrashReport'

    gameID              = models.IntegerField(default=0)
    description         = models.CharField(max_length=400)
    isdesync            = models.BooleanField(default=False)
    gistID              = models.IntegerField(default=0)
