import os
import shutil
from django.conf import settings
from openra.models import Maps
from openra import misc
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):

	def handle(self, *args, **options):
		self.SyncMapsWithRsyncDirs()

	def SyncMapsWithRsyncDirs(self):
		# this function syncs rsync directories with fresh list of maps, triggered by uploading a new map or removing one
		if settings.RSYNC_MAP_PATH.strip() == "":
			return

		mods = Maps.objects.values_list('game_mod', flat=True).distinct()

		all_Local_MapsID = {}
		for mod in mods:
			try:
				os.makedirs(settings.RSYNC_MAP_PATH + mod.lower())
			except:
				# get list of all local map ids
				listLocal = os.listdir(settings.RSYNC_MAP_PATH + mod.lower())
				for itm in listLocal:
					all_Local_MapsID[ int(itm.split('.')[0]) ] = mod.lower()

		# object: container of all accepted for rsync maps
		mapObject = Maps.objects.filter(requires_upgrade=False,downloading=True,players__gte=1,rsync_allow=True,amount_reports__lt=settings.REPORTS_PENALTY_AMOUNT,next_rev=0).distinct("map_hash")
		all_Remote_MapsID = [m.id for m in mapObject]

		# delete outdated local maps
		# for duplicates, fetching distinct by hash map, it behaves unpredictably and can remove one and then put another
		removed = ""
		for mID in all_Local_MapsID:
			if mID not in all_Remote_MapsID:
				os.remove(settings.RSYNC_MAP_PATH + all_Local_MapsID[mID] + '/' + str(mID) + '.oramap')
				removed += all_Local_MapsID[mID] + '/' + str(mID) + '.oramap '
		if removed != "":
			misc.Log("Removed maps on syncing maps with rsync directory: " + removed.strip(), 'rsync')

		site_path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/maps/'
		for item in mapObject:
			listd = os.listdir(site_path + str(item.id))
			for fname in listd:
				if fname.endswith('.oramap'):
					src = site_path + str(item.id) + '/' + fname
					dest_maps = settings.RSYNC_MAP_PATH + item.game_mod.lower() + '/' + str(item.id) + '.oramap'
					if not os.path.exists(dest_maps):
						os.link(src, dest_maps)
					break
			continue