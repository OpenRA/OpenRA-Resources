from django.conf import settings
from django.contrib.auth.models import User
from openraData.models import Maps

# Map Triggers

def recalculate_hashes():
    # this function recalculates hashes for all existing maps and updates DB
    pass

def map_upgrade():
    # this function upgrades all existings maps using OpenRA.Utility and triggers recalculate_hashes() function
    pass

def filterMapsRsync():
	# sync + syncall
	# this function syncs rsync directory with fresh list of maps, triggered by uploading a new map
	pass

def LintCheck():
	# weekly, this function performs a Lint Check for all existing maps