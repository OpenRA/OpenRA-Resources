from django.db import models
from django.contrib.auth.models import User

class Maps(models.Model):
    user        = models.ForeignKey(User)
    title       = models.CharField(max_length=200)
    description = models.CharField(max_length=400)
    info        = models.CharField(max_length=400)
    author      = models.CharField(max_length=40)
    type        = models.CharField(max_length=40)
    players     = models.IntegerField(default=0)
    game_mod    = models.CharField(max_length=16)
    map_hash    = models.CharField(max_length=40)
    width       = models.CharField(max_length=16)
    height      = models.CharField(max_length=16)
    tileset     = models.CharField(max_length=16)
    posted      = models.DateTimeField('date published')
    revision    = models.IntegerField(default=1)
    pre_rev     = models.IntegerField(default=0)
    next_rev    = models.IntegerField(default=0)
    downloading = models.BooleanField(default=True)
    viewed      = models.IntegerField(default=0)

class Units(models.Model):
    user        = models.ForeignKey(User)
    title       = models.CharField(max_length=200)
    info        = models.CharField(max_length=400)
    type        = models.CharField(max_length=16)
    category    = models.CharField(max_length=16)
    palette     = models.CharField(max_length=16)
    posted      = models.DateTimeField('date published')
    viewed      = models.IntegerField(default=0)

class Palettes(models.Model):
    user        = models.ForeignKey(User)
    title       = models.CharField(max_length=200)
    info        = models.CharField(max_length=400)
    used        = models.IntegerField(default=0)
    posted      = models.DateTimeField('date published')

class Reports(models.Model):
    user        = models.ForeignKey(User)
    reason      = models.CharField(max_length=400)
    ex_id       = models.IntegerField(default=0)
    ex_name     = models.CharField(max_length=16)
    posted      = models.DateTimeField('date published')

class Comments(models.Model):
    user        = models.ForeignKey(User)
    message     = models.CharField(max_length=400)
    ex_id       = models.IntegerField(default=0)
    ex_name     = models.CharField(max_length=16)
    posted      = models.DateTimeField('date published')

class Screenshots(models.Model):
    user        = models.ForeignKey(User)
    ex_id       = models.IntegerField(default=0)
    ex_name     = models.CharField(max_length=16)
    posted      = models.DateTimeField('date published')
    map_preview = models.BooleanField(default=False)
