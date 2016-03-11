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
	description         = models.CharField(max_length=4000)
	info                = models.CharField(max_length=4000)
	author              = models.CharField(max_length=200)
	map_type            = models.CharField(max_length=100)
	players             = models.IntegerField(default=0)
	game_mod            = models.CharField(max_length=100)
	map_hash            = models.CharField(max_length=200)
	width               = models.CharField(max_length=16)
	height              = models.CharField(max_length=16)
	bounds              = models.CharField(max_length=50,default="")
	tileset             = models.CharField(max_length=50)
	spawnpoints         = models.CharField(max_length=1000,default="")
	mapformat           = models.IntegerField(default=6)
	parser              = models.CharField(max_length=100, default="release-20141029")
	shellmap            = models.BooleanField(default=False)
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
	policy_adaptations  = models.CharField(max_length=30)
	policy_commercial   = models.BooleanField(default=False)



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



class Replays(models.Model):

	class Meta:
		verbose_name_plural = 'Replays'

	def __str__(self):
		return str(self.id)

	user                = models.ForeignKey(User)
	info                = models.CharField(max_length=2000, default="")
	metadata            = models.CharField(max_length=100000, default="")

	game_mod            = models.CharField(max_length=100, default="")
	map_hash            = models.CharField(max_length=200, default="")
	version             = models.CharField(max_length=100, default="release-20141029")
	start_time          = models.CharField(max_length=50, default="")
	end_time            = models.CharField(max_length=50, default="")

	sha1sum             = models.CharField(max_length=200, default="")
	parser              = models.CharField(max_length=100, default="release-20141029")
	posted              = models.DateTimeField('date published', default=datetime.datetime.now)
	viewed              = models.IntegerField(default=0)
	downloaded          = models.IntegerField(default=0)
	rating              = models.FloatField(default=0.0)



class ReplayPlayers(models.Model):

	class Meta:
		verbose_name_plural = "ReplayPlayers"

	def __str__(self):
		return 'replay_id: ' + str(self.replay_id)

	user                = models.ForeignKey(User)
	replay_id           = models.IntegerField(default=0)

	client_index        = models.IntegerField(default=0)
	color               = models.CharField(max_length=30)
	faction_id          = models.CharField(max_length=50)
	faction_name        = models.CharField(max_length=50)
	is_bot              = models.BooleanField(default=False)
	is_human            = models.BooleanField(default=True)
	is_random_faction   = models.BooleanField(default=False)
	is_random_spawn     = models.BooleanField(default=False)
	name                = models.CharField(max_length=1000)
	outcome             = models.CharField(max_length=50)
	outcome_timestamp   = models.CharField(max_length=50)
	spawn_point         = models.IntegerField(default=0)
	team                = models.IntegerField(default=0)

	posted              = models.DateTimeField('date published', default=datetime.datetime.now)



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
