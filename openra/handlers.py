import shutil
import os
import zipfile
import string
import re
import signal
import random
import yaml
import json
from subprocess import Popen, PIPE
import multiprocessing
from pgmagick import Image, ImageList, Geometry, FilterTypes, Blob

from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from openra.models import Maps, Replays, ReplayPlayers, Lints, Screenshots
from openra import utility, misc

class ReplayHandlers():

	def __init__(self):
		self.replay_is_uploaded = False
		self.UID = False
		self.currentDirectory = os.getcwd() + os.sep    # web root

	def process_uploading(self, user_id, replay_file, post):

		parser_to_db = list(reversed( list(settings.OPENRA_VERSIONS.values()) ))[0] # default parser = the latest
		parser = settings.OPENRA_ROOT_PATH + parser_to_db

		if post.get("parser", None) != None:
			parser_to_db = post['parser']
			parser = settings.OPENRA_ROOT_PATH + parser_to_db
			if 'git' in parser:
				parser = settings.OPENRA_BLEED_PARSER

		response = {'error': False, 'response': ''}
		tempname = '/tmp/' + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8)) + '.orarep'
		with open(tempname, 'wb+') as destination:
			for chunk in replay_file.chunks():
				destination.write(chunk)

		command = 'file -b --mime-type %s' % tempname
		proc = Popen(command.split(), stdout=PIPE).communicate()
		mimetype = proc[0].decode().strip()
		if not ( (mimetype == 'application/octet-stream' or mimetype == 'application/zip') and os.path.splitext(replay_file.name)[1].lower() == '.orarep' ):
			response['error'] = True
			response['response'] = 'Failed. Unsupported file type.'
			return response

		command = 'sha1sum %s' % tempname
		proc = Popen(command.split(), stdout=PIPE).communicate()
		sha1_hash = proc[0].decode().split()[0].strip()

		sha1sum_exists = Replays.objects.filter(sha1sum=sha1_hash,user=user_id)
		if sha1sum_exists:
			response['error'] = True
			response['response'] = 'Failed. You have already uploaded this replay.'
			return response


		replay_metadata = self.get_replay_metadata(tempname, parser)

		if not replay_metadata:
			response['error'] = True
			response['response'] = 'Failed to fetch replay metadata.'
			return response

		userObject = User.objects.get(pk=user_id)
		transac = Replays(
			user = userObject,
			info = post['replay_info'].strip(),
			metadata = json.dumps(replay_metadata),

			game_mod = replay_metadata['Mod'],
			map_hash = replay_metadata['MapUid'],
			version = replay_metadata['Version'],
			start_time = replay_metadata['StartTimeUtc'],
			end_time = replay_metadata['EndTimeUtc'],

			sha1sum = sha1_hash,
			parser = parser_to_db,
			posted = timezone.now(),
		)
		transac.save()
		self.UID = transac.id

		for pl_key, pl_value in replay_metadata['Players'].items():
			transac_player = ReplayPlayers(
				user = userObject,
				replay_id = transac.id,

				client_index = replay_metadata['Players'][pl_key]['ClientIndex'],
				color = replay_metadata['Players'][pl_key]['Color'],
				faction_id = replay_metadata['Players'][pl_key]['FactionId'],
				faction_name = replay_metadata['Players'][pl_key]['FactionName'],
				is_bot = replay_metadata['Players'][pl_key]['IsBot'],
				is_human = replay_metadata['Players'][pl_key]['IsHuman'],
				is_random_faction = replay_metadata['Players'][pl_key]['IsRandomFaction'],
				is_random_spawn = replay_metadata['Players'][pl_key]['IsRandomSpawnPoint'],
				name = replay_metadata['Players'][pl_key]['Name'],
				outcome = replay_metadata['Players'][pl_key]['Outcome'],
				outcome_timestamp = replay_metadata['Players'][pl_key]['OutcomeTimestampUtc'],
				spawn_point = replay_metadata['Players'][pl_key]['SpawnPoint'],
				team = replay_metadata['Players'][pl_key]['Team'],

				posted = timezone.now(),
			)
			transac_player.save()

		replay_directory = self.currentDirectory + __name__.split('.')[0] + '/data/replays/' + str(self.UID) + '/'
		if not os.path.exists( replay_directory ):
			os.makedirs( replay_directory )

		shutil.move(tempname, replay_directory + str(self.UID) + '.orarep')

		self.replay_is_uploaded = True

		response['error'] = False
		response['response'] = replay_metadata
		return response

	def get_replay_metadata(self, fullpath, parser=settings.OPENRA_ROOT_PATH + list(reversed( list(settings.OPENRA_VERSIONS.values()) ))[0]):
		os.chdir(parser + "/")

		command = 'mono --debug OpenRA.Utility.exe ra --replay-metadata ' + fullpath
		proc = Popen(command.split(), stdout=PIPE).communicate()

		replay_metadata = ""
		for res in proc:
			if res == None:
				continue
			lines = res.decode().split("\n")
			for line in lines:
				if '.orarep' in line:
					continue
				else:
					if line.strip() != "":
						replay_metadata += line + "\n"

		replay_metadata = yaml.load(re.sub('\t', '    ', replay_metadata))

		os.chdir(self.currentDirectory)
		return replay_metadata


class MapHandlers():
	
	def __init__(self, map_full_path_filename="", map_full_path_directory="", preview_filename=""):
		self.map_is_uploaded = False
		self.minimap_generated = False
		self.maphash = ""
		self.LintPassed = False
		self.advanced_map = False
		self.lua_map = False
		self.map_full_path_directory = map_full_path_directory
		self.map_full_path_filename = map_full_path_filename
		self.preview_filename = preview_filename
		self.currentDirectory = os.getcwd() + os.sep    # web root
		self.UID = False
		self.legacy_name = ""
		self.legacy_map = False

	def ProcessUploading(self, user_id, f, post, rev=1, pre_r=0):

		parser_to_db = list(reversed( list(settings.OPENRA_VERSIONS.values()) ))[0] # default parser = the latest
		parser = settings.OPENRA_ROOT_PATH + parser_to_db

		if post.get("parser", None) != None:
			parser_to_db = post['parser']
			parser = settings.OPENRA_ROOT_PATH + parser_to_db
			if 'git' in parser:
				parser = settings.OPENRA_BLEED_PARSER

		if pre_r != 0:
			mapObject = Maps.objects.filter(id=pre_r, user_id=user_id)
			if not mapObject:
				return 'Failed. You do not own map for which you want to upload a new revision.'
			if mapObject[0].next_rev != 0:
				return 'Failed. Unable to upload a new revision for map which already has one.'
			previous_policy_cc = mapObject[0].policy_cc
			previous_policy_commercial = mapObject[0].policy_commercial
			previous_policy_adaptations = mapObject[0].policy_adaptations
		tempname = '/tmp/openramap.oramap'
		with open(tempname, 'wb+') as destination:
			for chunk in f.chunks():
				destination.write(chunk)

		command = 'file -b --mime-type %s' % tempname
		proc = Popen(command.split(), stdout=PIPE).communicate()
		mimetype = proc[0].decode().strip()
		if not ( mimetype == 'application/zip' and os.path.splitext(f.name)[1].lower() == '.oramap' ):
			if not ( mimetype == 'text/plain' and os.path.splitext(f.name)[1].lower() in ['.mpr', '.ini'] ):
				return 'Failed. Unsupported file type.'

		name = f.name
		badChars = ": ; < > @ $ # & ( ) % '".split()
		for badchar in badChars:
			name = name.replace(badchar, "_")
		name = name.replace(" ", "_")
		# There can be weird chars still, if so: stop uploading
		findBadChars = re.findall(r'(\W+)', name)
		for bc in findBadChars:
			if bc not in ['.','-']:
				return 'Failed. Your filename is bogus; rename and try again.'

		if mimetype == 'text/plain':
			if not self.LegacyImport(tempname, parser):
				misc.send_email_to_admin_OnMapFail(tempname)
				return 'Failed to import legacy map.'
			shutil.move(parser + "/" + self.legacy_name, tempname)
			name = os.path.splitext(name)[0] + '.oramap'
			self.legacy_map = True

		### Check if user has already uploaded the same map
		self.GetHash(tempname, parser)
		if 'Converted' in self.maphash and 'to MapFormat' in self.maphash:
			misc.send_email_to_admin_OnMapFail(tempname)
			return 'Failed to upload with this parser. MapFormat does not match. Try to upgrade your map or use different parser.'

		userObject = User.objects.get(pk=user_id)
		try:
			hashExists = Maps.objects.get(user_id=userObject.id, map_hash=self.maphash)
			self.UID = str(hashExists.id)
			return "Failed. You've already uploaded this map."
		except:
			pass   # all good

		### Read Yaml ###
		read_yaml_response = utility.ReadYaml(False, tempname)
		resp_map_data = read_yaml_response['response']
		if read_yaml_response['error']:
			misc.send_email_to_admin_OnMapFail(tempname)
			return resp_map_data

		### Define license information
		cc = False
		commercial = False
		adaptations = ""
		if pre_r == 0:
			if post['policy_cc'] == 'cc_yes':
				cc = True
				if post['commercial'] == "com_yes":
					commercial = True
				if post['adaptations'] == "adapt_yes":
					adaptations = "yes"
				elif post['adaptations'] == "adapt_no":
					adaptations = "no"
				else:
					adaptations = "yes and shared alike"
		else:
			cc = previous_policy_cc
			commercial = previous_policy_commercial
			adaptations = previous_policy_adaptations


		### Add record to Database
		transac = Maps(
			user = userObject,
			title = resp_map_data['title'],
			description = resp_map_data['description'],
			info = post['info'].strip(),
			author = resp_map_data['author'],
			map_type = resp_map_data['map_type'],
			categories = resp_map_data['categories'],
			players = resp_map_data['players'],
			game_mod = resp_map_data['game_mod'],
			map_hash = self.maphash.strip(),
			width = resp_map_data['width'],
			height = resp_map_data['height'],
			bounds = resp_map_data['bounds'],
			mapformat = resp_map_data['mapformat'],
			spawnpoints = resp_map_data['spawnpoints'],
			tileset = resp_map_data['tileset'],
			shellmap = resp_map_data['shellmap'],
			legacy_map = self.legacy_map,
			revision = rev,
			pre_rev = pre_r,
			next_rev = 0,
			downloading = True,
			requires_upgrade = not self.LintPassed,
			advanced_map = resp_map_data['advanced'],
			lua = resp_map_data['lua'],
			posted = timezone.now(),
			viewed = 0,
			policy_cc = cc,
			policy_commercial = commercial,
			policy_adaptations = adaptations,
			parser = parser_to_db,
		)
		transac.save()
		self.UID = str(transac.id)
		if pre_r != 0:
			Maps.objects.filter(id=pre_r).update(next_rev=transac.id)

		self.map_full_path_directory = self.currentDirectory + __name__.split('.')[0] + '/data/maps/' + self.UID + '/'
		if not os.path.exists(self.map_full_path_directory):
			os.makedirs(self.map_full_path_directory + 'content')
		self.map_full_path_filename = self.map_full_path_directory + name
		self.preview_filename = os.path.splitext(name)[0] + ".png"

		shutil.move(tempname, self.map_full_path_filename)

		self.map_is_uploaded = True

		self.UnzipMap()

		lint_check_response = utility.LintCheck(transac, self.map_full_path_filename, parser)
		if lint_check_response['error'] == False and lint_check_response['response'] == 'pass_for_requested_parser':
			self.LintPassed = True

		if self.LintPassed:
			Maps.objects.filter(id=transac.id).update(requires_upgrade=False)
		else:
			Maps.objects.filter(id=transac.id).update(requires_upgrade=True)

		if int(resp_map_data['mapformat']) < 10:
			self.GenerateMinimap(resp_map_data['game_mod'], parser)

		shp = multiprocessing.Process(target=self.GenerateSHPpreview, args=(resp_map_data['game_mod'], parser,), name='shppreview')
		shp.start()
		print("--- New map: %s" % self.UID)
		return False # no errors

	def UnzipMap(self):
		z = zipfile.ZipFile(self.map_full_path_filename, mode='a')
		try:
			z.extractall(self.map_full_path_directory + 'content/')
		except:
			pass
		z.close()

	def GetHash(self, filepath="", parser=settings.OPENRA_ROOT_PATH + list(reversed( list(settings.OPENRA_VERSIONS.values()) ))[0]):
		if filepath == "":
			filepath = self.map_full_path_filename

		os.chdir(parser + "/")

		os.chmod(filepath, 0o444)

		command = 'mono --debug OpenRA.Utility.exe ra --map-hash ' + filepath
		proc = Popen(command.split(), stdout=PIPE).communicate()

		os.chmod(filepath, 0o644)

		self.maphash = proc[0].decode().strip()

		os.chdir(self.currentDirectory)

	def GenerateMinimap(self, game_mod, parser=settings.OPENRA_ROOT_PATH + list(reversed( list(settings.OPENRA_VERSIONS.values()) ))[0]):
		os.chdir(parser + "/")

		os.chmod(self.map_full_path_filename, 0o444)
		command = 'mono --debug OpenRA.Utility.exe %s --map-preview %s' % (game_mod, self.map_full_path_filename)
		proc = Popen(command.split(), stdout=PIPE).communicate()
		os.chmod(self.map_full_path_filename, 0o644)

		try:
			shutil.move(misc.addSlash(parser + "/") + self.preview_filename,
				self.map_full_path_directory + os.path.splitext(self.preview_filename)[0] + "-mini.png")
			self.minimap_generated = True
		except:
			pass # failed to generate minimap

		os.chdir(self.currentDirectory)

	def GenerateSHPpreview(self, game_mod, parser=settings.OPENRA_ROOT_PATH + list(reversed( list(settings.OPENRA_VERSIONS.values()) ))[0]):
		Dir = os.listdir(self.map_full_path_directory+'content/')
		for fn in Dir:
			if fn.endswith('.shp'):
				os.mkdir(self.map_full_path_directory+'content/png/')
				os.chdir(self.map_full_path_directory+'content/png/')
				command = 'mono --debug %sOpenRA.Utility.exe %s --png %s %s' % (parser + "/", game_mod, self.map_full_path_directory+'content/'+fn, '../../../../palettes/0/RA1/temperat.pal')

				class TimedOut(Exception): # Raised if timed out.
					pass

				def signal_handler(signum, frame):
					raise TimedOut("Timed out!")

				signal.signal(signal.SIGALRM, signal_handler)

				signal.alarm(settings.UTILITY_TIME_LIMIT)    # Limit command execution time

				try:
					proc = Popen(command.split(), stdout=PIPE).communicate()
					signal.alarm(0)
				except:
					err = 'Error: failed to generate SHP preview for %s (map: %s)' % (fn, self.UID)
					print(err)
					misc.send_email_to_admin('ORC: Failed to generate SHP preview', '%s \n\n %s' % (err, command))

					os.chdir(self.currentDirectory)
					shutil.rmtree(self.map_full_path_directory+'content/png/')

					continue
				pngsdir = os.listdir(self.map_full_path_directory+'content/png/')
				imglist = []
				for pngfn in pngsdir:
					if pngfn.endswith('.png'):
						imglist.append(pngfn)
				imglist.sort()
				imgs = ImageList()
				for img in imglist:
					imgs.append(Image(self.map_full_path_directory+'content/png/'+img))
				imgs.animationDelayImages(50)
				imgs.writeImages(self.map_full_path_directory+'content/'+fn+'.gif')
				os.chdir(self.currentDirectory)
				shutil.rmtree(self.map_full_path_directory+'content/png/')
		exit()

	def LegacyImport(self, mapPath, parser=settings.OPENRA_ROOT_PATH + list(reversed( list(settings.OPENRA_VERSIONS.values()) ))[0]):
		os.chdir(parser + "/")
		for mod in ['ra','cnc']:

			assign_mod = mod
			if mod == 'cnc':
				assign_mod = 'td'

			pre_command = 'mono --debug OpenRA.Utility.exe ra'
			pre_proc = Popen(pre_command.split(), stdout=PIPE).communicate()
			if '--import-' in pre_proc[0].decode():
				command = 'mono --debug OpenRA.Utility.exe %s --import-%s-map %s' % (mod, assign_mod, mapPath)
			else:
				command = 'mono --debug OpenRA.Utility.exe %s --map-import %s' % (mod, mapPath)

			proc = Popen(command.split(), stdout=PIPE).communicate()

			if "Error" in proc[0].decode():
				continue
			else:
				if "saved" in proc[0].decode():
					self.legacy_name = proc[0].decode().split("\n")[-2].split(' saved')[0]
					os.chdir(self.currentDirectory)
					return True
				else:
					continue
		os.chdir(self.currentDirectory)
		return False



def addScreenshot(f, arg, user_id, item):
	if item == 'map':
		Object = Maps.objects.filter(id=arg)
		if not Object:
			return False
		if not (Object[0].user_id == user_id.id or user_id.is_superuser):
			return False
	else:
		return False
	tempname = '/tmp/screenshot.temp'
	with open(tempname, 'wb+') as destination:
		for chunk in f.chunks():
			destination.write(chunk)

	command = 'file -b --mime-type %s' % tempname
	proc = Popen(command.split(), stdout=PIPE).communicate()
	mimetype = proc[0].decode().strip()
	if mimetype not in ['image/jpeg','image/png','image/gif']:
		return False

	transac = Screenshots(
		user = Object[0].user,
		ex_id = int(arg),
		ex_name = item+"s",
		posted =  timezone.now(),
		map_preview = False,
		)
	transac.save()

	path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/screenshots/' + str(transac.id) + '/'
	if not os.path.exists(path):
		os.makedirs(path)

	shutil.move(tempname, path + arg + "." + mimetype.split('/')[1])


	command = 'identify -format "%w,%h" {0}'.format(path + arg + "." + mimetype.split('/')[1])
	proc = Popen(command.split(), stdout=PIPE).communicate()
	details = proc[0].decode().strip().strip('"').split(',')

	im = Image( str(path + arg + "." + mimetype.split('/')[1]) )
	
	scaleH = int(details[0]) / 100.0
	scaleH = 250 / scaleH
	scaleH = int(details[1]) / 100.0 * scaleH

	im.quality(100)
	im.filterType(FilterTypes.SincFilter)
	im.scale('250x%s' % scaleH)
	im.sharpen(1.0)
	im.write(str(path + arg + "-mini." + mimetype.split('/')[1]))
