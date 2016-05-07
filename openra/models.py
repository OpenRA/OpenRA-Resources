from django.db import models
from django.contrib.auth.models import User
import datetime


class Maps(models.Model):

    class Meta:
        verbose_name_plural = 'Maps'

    def __str__(self):
        return str(self.id)

    user                = models.ForeignKey(User)
    title               = models.CharField(max_length=200)
    description         = models.CharField(max_length=4000, blank=True, null=True)
    info                = models.CharField(max_length=4000, blank=True, null=True)
    author              = models.CharField(max_length=200)
    map_type            = models.CharField(max_length=100, blank=True, null=True)
    categories          = models.CharField(max_length=200, blank=True, null=True)
    players             = models.IntegerField(default=0)
    game_mod            = models.CharField(max_length=100)
    map_hash            = models.CharField(max_length=200)
    width               = models.CharField(max_length=16)
    height              = models.CharField(max_length=16)
    bounds              = models.CharField(max_length=50, default="")
    tileset             = models.CharField(max_length=50)
    spawnpoints         = models.CharField(max_length=1000, default="")
    mapformat           = models.IntegerField(default=6)
    parser              = models.CharField(max_length=100, default="release-20141029")
    shellmap            = models.BooleanField(default=False)
    base64_rules        = models.CharField(max_length=1000000, blank=True, null=True, default="")
    base64_players      = models.CharField(max_length=1000000, blank=True, null=True, default="")
    legacy_map          = models.BooleanField(default=False)
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
    rating              = models.FloatField(default=0.0)
    rsync_allow         = models.BooleanField(default=True)
    amount_reports      = models.IntegerField(default=0)
    policy_cc           = models.BooleanField(default=False)
    policy_adaptations  = models.CharField(max_length=30, blank=True, null=True)
    policy_commercial   = models.BooleanField(default=False)
    last_for_rsync      = models.BooleanField(default=False)  # temp field, required for upgrade from release 20151224


class MapCategories(models.Model):

    class Meta:
        verbose_name_plural = 'MapCategories'

    def __str__(self):
        return self.category_name

    category_name       = models.CharField(max_length=100)
    posted              = models.DateTimeField('dated added', default=datetime.datetime.now)


class Lints(models.Model):

    class Meta:
        verbose_name_plural = 'Lints'

    item_type           = models.CharField(max_length=16, default="maps")
    map_id              = models.IntegerField(default=0)
    version_tag         = models.CharField(max_length=100, default="release-20141029")
    pass_status         = models.BooleanField(default=False)
    lint_output         = models.CharField(max_length=1000000, default="")
    posted              = models.DateTimeField('date of check')


class Comments(models.Model):

    class Meta:
        verbose_name_plural = 'Comments'

    def __str__(self):
        return self.item_type + ' ' + str(self.item_id) + ' by ' + self.user.username

    user                = models.ForeignKey(User)
    content             = models.CharField(max_length=10000)
    item_type           = models.CharField(max_length=16, default="maps")
    item_id             = models.IntegerField(default=0)
    posted              = models.DateTimeField('date of comment')
    is_removed          = models.BooleanField(default=False)


class UnsubscribeComments(models.Model):

    class Meta:
        verbose_name_plural = 'Unsubscribed From Comments'

    def __str__(self):
        return str(self.id)

    user                = models.ForeignKey(User)
    item_type           = models.CharField(max_length=16, default="maps")
    item_id             = models.IntegerField(default=0)
    unsubscribed        = models.DateTimeField('date of unsubscribe')


class Reports(models.Model):

    class Meta:
        verbose_name_plural = 'Reports'

    user                = models.ForeignKey(User)
    reason              = models.CharField(max_length=400)
    ex_id               = models.IntegerField(default=0)
    ex_name             = models.CharField(max_length=16)
    infringement        = models.BooleanField(default=False)
    posted              = models.DateTimeField('date published')


class Screenshots(models.Model):

    class Meta:
        verbose_name_plural = 'Screenshots'

    user                = models.ForeignKey(User)
    ex_id               = models.IntegerField(default=0)
    ex_name             = models.CharField(max_length=16)
    posted              = models.DateTimeField('date published')
    map_preview         = models.BooleanField(default=False)


class Rating(models.Model):

    class Meta:
        verbose_name_plural = 'Ratings'

    user                = models.ForeignKey(User)
    ex_id               = models.IntegerField(default=0)
    ex_name             = models.CharField(max_length=16)
    rating              = models.FloatField(default=0.0)
    posted              = models.DateTimeField('date rated')
