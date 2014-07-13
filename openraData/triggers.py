import os
import shutil
import zipfile
import string
from pgmagick import Image, ImageList, Geometry, FilterTypes, Blob
from subprocess import Popen, PIPE
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Count
from django.utils import timezone
from openraData.models import Maps, Screenshots, Reports
from openraData import misc

# Map Triggers

def map_upgrade(mapObject, engine, http_host):
	currentDirectory = os.getcwd() + os.sep
	for item in mapObject:
		os.chdir(settings.OPENRA_PATH)
		path = currentDirectory + 'openraData/data/maps/' + str(item.id) + '/'
		filename = ""
		Dir = os.listdir(path)
		for fn in Dir:
			if fn.endswith('.oramap'):
				filename = fn
				break
		if filename == "":
			continue
		command = 'mono OpenRA.Utility.exe --upgrade-map %s %s' % (path+filename, engine)
		print(command)
		proc = Popen(command.split(), stdout=PIPE).communicate()
		os.chdir(currentDirectory)

		maphash = recalculate_hash(item)
		lint_passed = not LintCheck([item], http_host)
		Maps.objects.filter(id=item.id).update(map_hash=maphash)
		Maps.objects.filter(id=item.id).update(requires_upgrade=lint_passed)

		if not UnzipMap(item):
			print("failed to unzip %s" % item.id)
			continue
		yamlread = ReadYamlAgain(item)
		if not yamlread:
			print("ReadYamlAgain: failed to read map or map.yaml")
			continue
	os.chdir(currentDirectory)
	return True

def recalculate_hash(mapObject):
	currentDirectory = os.getcwd() + os.sep
	os.chdir(settings.OPENRA_PATH)

	path = currentDirectory + 'openraData/data/maps/' + str(mapObject.id) + '/'
	filename = ""
	Dir = os.listdir(path)
	for fn in Dir:
		if fn.endswith('.oramap'):
			filename = fn
			break
	if filename == "":
		os.chdir(currentDirectory)
		return "none"
	command = 'mono OpenRA.Utility.exe --map-hash ' + path + filename
	proc = Popen(command.split(), stdout=PIPE).communicate()
	maphash = proc[0].strip()
	os.chdir(currentDirectory)
	return maphash

def ReadYamlAgain(mapObject):
	currentDirectory = os.getcwd() + os.sep
	path = currentDirectory + 'openraData/data/maps/' + str(mapObject.id) + '/'
	filename = ""
	Dir = os.listdir(path)
	for fn in Dir:
		if fn.endswith('.oramap'):
			filename = fn
			break
	if filename == "":
		return False
	z = zipfile.ZipFile(path + filename, mode='a')
	yamlData = ""
	for zfn in z.namelist():
		if zfn == "map.yaml":
			mapbytes = z.read(zfn)
			yamlData = mapbytes.decode("utf-8")
			break
	z.close()
	if yamlData == "":
		return False
	expectspawn = False
	spawnpoints = ""
	map_data_ordered = {}
	map_data_ordered['players'] = 0
	map_data_ordered['description'] = ""
	for line in string.split(yamlData, '\n'):
		if line[0:5] == "Title":
			map_data_ordered['title'] = line[6:].strip().replace("'", "''")
		if line[0:11] == "RequiresMod":
			map_data_ordered['game_mod'] = line[12:].strip().lower()
		if line[0:6] == "Author":
			map_data_ordered['author'] = line[7:].strip().replace("'", "''")
		if line[0:7] == "Tileset":
			map_data_ordered['tileset'] = line[8:].strip().lower()
		if line[0:4] == "Type":
			map_data_ordered['map_type'] = line[5:].strip()
		if line[0:11] == "Description":
			map_data_ordered['description'] = line[12:].strip().replace("'", "''")
		if line[0:7] == "MapSize":
			map_data_ordered['width'] = line[8:].strip().split(',')[0]
			map_data_ordered['height'] = line[8:].strip().split(',')[1]
		if line[0:6] == "Bounds":
			map_data_ordered['bounds'] = line[7:].strip()
		if line.strip()[-7:] == "mpspawn":
			expectspawn = True
		if line.strip()[0:8] == "Location":
			if expectspawn:
				spawnpoints += line.split(':')[1].strip()+","
				expectspawn = False
		if line.strip()[0:8] == "Playable":
			state = line.split(':')[1]
			if state.strip().lower() in ['true', 'on', 'yes', 'y']:
				map_data_ordered['players'] += 1
	map_data_ordered['spawnpoints'] = spawnpoints.rstrip(",")
	if len(map_data_ordered) == 0:
		return False
	Maps.objects.filter(id=mapObject.id).update(game_mod=map_data_ordered['game_mod'])
	Maps.objects.filter(id=mapObject.id).update(title=map_data_ordered['title'])
	Maps.objects.filter(id=mapObject.id).update(author=map_data_ordered['author'])
	Maps.objects.filter(id=mapObject.id).update(tileset=map_data_ordered['tileset'])
	Maps.objects.filter(id=mapObject.id).update(map_type=map_data_ordered['map_type'])
	Maps.objects.filter(id=mapObject.id).update(description=map_data_ordered['description'])
	Maps.objects.filter(id=mapObject.id).update(players=map_data_ordered['players'])
	Maps.objects.filter(id=mapObject.id).update(bounds=map_data_ordered['bounds'])
	Maps.objects.filter(id=mapObject.id).update(spawnpoints=map_data_ordered['spawnpoints'])
	Maps.objects.filter(id=mapObject.id).update(width=map_data_ordered['width'])
	Maps.objects.filter(id=mapObject.id).update(height=map_data_ordered['height'])
	return True

def UnzipMap(mapObject):
	currentDirectory = os.getcwd() + os.sep
	path = currentDirectory + 'openraData/data/maps/' + str(mapObject.id) + '/'
	filename = ""
	Dir = os.listdir(path)
	for fn in Dir:
		if fn.endswith('.oramap'):
			filename = fn
			break
	if filename == "":
		return False
	z = zipfile.ZipFile(path + filename, mode='a')
	z.extractall(path + 'content/')
	z.close()
	return True

def PushMapsToRsyncDirs():
	# this function syncs rsync directories with fresh list of maps, triggered by uploading a new map or removing one
	if settings.RSYNC_MAP_PATH.strip() == "":
		return
	mods = Maps.objects.values_list('game_mod', flat=True).distinct()
	RSYNC_MAP_PATH = misc.addSlash(settings.RSYNC_MAP_PATH)
	RSYNC_MAP_API_PATH = misc.addSlash(settings.RSYNC_MAP_API_PATH)
	if os.path.exists(RSYNC_MAP_PATH):
		shutil.rmtree(RSYNC_MAP_PATH)
	for mod in mods:
		os.makedirs(RSYNC_MAP_PATH + mod.lower())
	mapObject = Maps.objects.filter(requires_upgrade=False,downloading=True,players__gte=1,rsync_allow=True).distinct("map_hash")
	mapObjectCopy = []
	for item in mapObject:
		reportObject = Reports.objects.filter(ex_id=item.id,ex_name="maps")
		if len(reportObject) < 3:
			mapObjectCopy.append(item)
	mapObject = mapObjectCopy
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
	status = False

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
		print(command)
		proc = Popen(command.split(), stdout=PIPE).communicate()
		if proc[0].strip() == "":
			status = True
			if item.requires_upgrade:
				Maps.objects.filter(id=item.id).update(requires_upgrade=False)
		else:
			status = False
			print(proc)
			lintlog = open(path+'lintlog','w')
			lintlog.write(proc[0])
			lintlog.close()
			if not item.requires_upgrade:
				Maps.objects.filter(id=item.id).update(requires_upgrade=True)
				mail_addr = misc.return_email(item.user_id)
				if mail_addr != "":
					misc.send_email_to_user_OnLint(mail_addr, "Lint check failed for one of your maps: http://"+http_host+"/maps/"+str(item.id)+"/")
	os.chdir(cwd)
	return status

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

def GenerateMinimap(mapObject):
	currentDirectory = os.getcwd() + os.sep
	os.chdir(settings.OPENRA_PATH)
	path = currentDirectory + 'openraData/data/maps/' + str(mapObject.id) + os.sep
	filename = ""
	Dir = os.listdir(path)
	for fn in Dir:
		if fn.endswith('.oramap'):
			filename = fn
			break
	if filename == "":
		os.chdir(currentDirectory)
		return False
	command = 'mono OpenRA.Utility.exe --map-preview ' + path + filename
	proc = Popen(command.split(), stdout=PIPE).communicate()
	try:
		shutil.move(settings.OPENRA_PATH + os.path.splitext(filename)[0] + ".png", path + os.path.splitext(filename)[0] + "-mini.png")
		os.chdir(currentDirectory)
		return True
	except:
		os.chdir(currentDirectory)
		return False

def GenerateFullPreview(mapObject, userObject):
	currentDirectory = os.getcwd() + os.sep
	os.chdir(settings.OPENRA_PATH)
	path = currentDirectory + 'openraData/data/maps/' + str(mapObject.id) + os.sep
	filename = ""
	Dir = os.listdir(path)
	for fn in Dir:
		if fn.endswith('.oramap'):
			filename = fn
			break
	if filename == "":
		os.chdir(currentDirectory)
		return False
	command = 'mono OpenRA.Utility.exe --full-preview ' + path + filename
	proc = Popen(command.split(), stdout=PIPE).communicate()
	try:
		shutil.move(settings.OPENRA_PATH + os.path.splitext(filename)[0] + ".png", path + os.path.splitext(filename)[0] + "-full.png")
		transac = Screenshots(
				user = userObject,
				ex_id = mapObject.id,
				ex_name = "maps",
				posted =  timezone.now(),
				map_preview = True,
		)
		transac.save()
		os.chdir(currentDirectory)
		return True
	except:
		os.chdir(currentDirectory)
		return False
