from django.db import models, connection
from django.contrib.auth.models import User
from djangoratings.fields import RatingField

class Maps(models.Model):
    
    class Meta:
        verbose_name = 'Map'

    def mapVersionsHandlerInit():
        #functionInit = """
        #
        #"""
        #cursor = connection.cursor()
        #cursor.execute(functionInit)
        print("Created function GetMapVersions.")

    user                = models.ForeignKey(User)
    title               = models.CharField(max_length=200)
    description         = models.CharField(max_length=400)
    info                = models.CharField(max_length=400)
    author              = models.CharField(max_length=40)
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
    rating              = RatingField(range=5, allow_anonymous=True, use_cookies=True)

    # Uncomment next line to initialize map functions
    #mapVersionsHandlerInit()

class Units(models.Model):

    class Meta:
        verbose_name = 'Unit'

    user                = models.ForeignKey(User)
    title               = models.CharField(max_length=200)
    info                = models.CharField(max_length=400)
    unit_type           = models.CharField(max_length=16)
    category            = models.CharField(max_length=16)
    palette             = models.CharField(max_length=16)
    revision            = models.IntegerField(default=1)
    pre_rev             = models.IntegerField(default=0)
    next_rev            = models.IntegerField(default=0)
    posted              = models.DateTimeField('date published')
    viewed              = models.IntegerField(default=0)
    rating              = RatingField(range=5, allow_anonymous=True, use_cookies=True)

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
    rating              = RatingField(range=5, allow_anonymous=True, use_cookies=True)

class Palettes(models.Model):

    class Meta:
        verbose_name = 'Palette'

    user                = models.ForeignKey(User)
    title               = models.CharField(max_length=200)
    info                = models.CharField(max_length=400)
    used                = models.IntegerField(default=0)
    posted              = models.DateTimeField('date published')

class Reports(models.Model):

    class Meta:
        verbose_name = 'Report'

    user                = models.ForeignKey(User)
    reason              = models.CharField(max_length=400)
    ex_id               = models.IntegerField(default=0)
    ex_name             = models.CharField(max_length=16)
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
