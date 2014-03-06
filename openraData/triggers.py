import os
import shutil
from pgmagick import Image, ImageList, Geometry, FilterTypes, Blob
from subprocess import Popen, PIPE
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Count
from openraData.models import Maps
from openraData import misc

# Map Triggers

def map_upgrade(mapObject):
    # this function upgrades all existings maps using OpenRA.Utility
    pass

def recalculate_hash(mapObject):
    # this function recalculates hashes for all existing maps and updates DB
    pass

def ReadYamlAgain(mapObject):
	pass

def PushMapsToRsyncDirs():
	# this function syncs rsync directories with fresh list of maps, triggered by uploading a new map
	if settings.RSYNC_MAP_PATH.strip() == "":
		return
	mods = Maps.objects.values_list('game_mod', flat=True).distinct()
	RSYNC_MAP_PATH = misc.addSlash(settings.RSYNC_MAP_PATH)
	RSYNC_MAP_API_PATH = misc.addSlash(settings.RSYNC_MAP_API_PATH)
	if os.path.exists(RSYNC_MAP_PATH):
		shutil.rmtree(RSYNC_MAP_PATH)
	for mod in mods:
		os.makedirs(RSYNC_MAP_PATH + mod.lower())
	mapObject = Maps.objects.filter(requires_upgrade=False,downloading=True,players__gte=1).distinct("map_hash")
	site_path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/maps/'
	if os.path.exists(RSYNC_MAP_API_PATH):
		shutil.rmtree(RSYNC_MAP_API_PATH)
	os.mkdir(RSYNC_MAP_API_PATH)
	for item in mapObject:
		listd = os.listdir(site_path + str(item.id))
		for fname in listd:
			if fname.endswith('.oramap'):
				src = site_path + str(item.id) + '/' + fname
				if item.next_rev == 0:
					dest_maps = RSYNC_MAP_PATH + item.game_mod.lower() + '/' + str(item.id) + '.oramap'
					os.link(src, dest_maps)
				dest_api_maps = RSYNC_MAP_API_PATH + item.map_hash + '_' + os.path.splitext(fname)[0] + '-' + str(item.revision) + '.oramap'
				os.link(src, dest_api_maps)
				break
		continue

def LintCheck(mapObject, http_host):
	# this function performs a Lint Check for all existing maps
	cwd = os.getcwd()
	os.chdir(settings.OPENRA_PATH)

	for item in mapObject:
		path = cwd + os.sep + __name__.split('.')[0] + '/data/maps/' + str(item.id) + os.sep
		listdir = os.listdir(path)
		map_file = ""
		for filename in listdir:
			if filename.endswith('.oramap'):
				map_file = filename
				break
		if map_file == "":
			continue
		command = 'mono OpenRA.Lint.exe ' + item.game_mod.lower() + ' ' + path + map_file
		proc = Popen(command.split(), stdout=PIPE).communicate()
		if proc[0].strip() == "":
			if item.requires_upgrade:
				Maps.objects.filter(id=item.id).update(requires_upgrade=False)
		else:
			if not item.requires_upgrade:
				Maps.objects.filter(id=item.id).update(requires_upgrade=True)
				userObject = User.objects.get(pk=item.user_id)
				if userObject.email != "":
					misc.send_email_to_user_OnLint(userObject.email, "Lint check failed for one of your maps: http://"+http_host+"/maps/"+str(item.id)+"/")
	return True

def GenerateSHPpreview(mapObject):
	# generates gif preview of shp files for every mapObject in list of objects
	currentDirectory = os.getcwd()
	for item in mapObject:
		path = os.getcwd() + os.sep + 'openraData/data/maps/' + str(item.id) + os.sep
		Dir = os.listdir(path + 'content/')
		for fn in Dir:
			if fn.endswith('.shp'):
				os.mkdir(path + 'content/png/')
				os.chdir(path + 'content/png/')
				command = 'mono %sOpenRA.Utility.exe --png %s %s' % (settings.OPENRA_PATH, path+'content/'+fn, '../../../../palettes/0/RA1/temperat.pal')
				proc = Popen(command.split(), stdout=PIPE).communicate()
				pngsdir = os.listdir(path + 'content/png/')
				imglist = []
				for pngfn in pngsdir:
					if pngfn.endswith('.png'):
						imglist.append(pngfn)
				imglist.sort()
				imgs = ImageList()
				for img in imglist:
					imgs.append(Image(path+'content/png/'+img))
				imgs.animationDelayImages(50)
				imgs.writeImages(path+'content/'+fn+'.gif')
				os.chdir(currentDirectory)
				shutil.rmtree(path+'content/png/')
	return True