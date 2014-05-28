import os
import json
import base64
import zipfile
import urllib2
from subprocess import Popen, PIPE
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404
from django.http import HttpResponse, HttpResponseRedirect, StreamingHttpResponse
from django.db.models import Count

from openraData.models import Maps
from openraData.models import CrashReports
from django.contrib.auth.models import User
from openraData import misc

# Map API
def mapAPI(request, arg, arg1="", arg2="", arg3="", arg4=""):
	# get detailed map info by title
	if arg == "title":
		title = arg1.lower()
		mapObject = Maps.objects.filter(title__icontains=title)
		if not mapObject:
			raise Http404
		if arg2 == "yaml":
			yaml_response = ""
			for item in mapObject:
				yaml_response += serialize_basic_map_info(request, item, "yaml")
			response = StreamingHttpResponse(yaml_response, content_type="text/plain")
			response['Access-Control-Allow-Origin'] = '*'
			return response
		else:
			json_response = []
			for item in mapObject:
				json_response.append(serialize_basic_map_info(request, item))
			response = StreamingHttpResponse(json.dumps(json_response), content_type="application/javascript")
			response['Access-Control-Allow-Origin'] = '*'
			return response
	
	# get detailed map info by hash
	elif arg == "hash":
		map_hashes = arg1.split(',')
		mapObject = Maps.objects.filter(map_hash__in=map_hashes)
		if not mapObject:
			raise Http404
		if arg2 == "yaml":
			yaml_response = ""
			for item in mapObject:
				yaml_response += serialize_basic_map_info(request, item, "yaml")
			if yaml_response == "":
				raise Http404
			response = StreamingHttpResponse(yaml_response, content_type="text/plain")
			response['Access-Control-Allow-Origin'] = '*'
			return response
		else:
			json_response = []
			for item in mapObject:
				json_response.append(serialize_basic_map_info(request, item))
			if len(json_response) == 0:
				raise Http404
			response = StreamingHttpResponse(json.dumps(json_response), content_type="application/javascript")
			response['Access-Control-Allow-Origin'] = '*'
			return response
	
	# get URL of map by hash
	elif arg == "url":
		map_hashes = arg1.split(',')
		mapObject = Maps.objects.filter(map_hash__in=map_hashes)
		if not mapObject:
			raise Http404
		if arg2 == "yaml":
			yaml_response = ""
			for item in mapObject:
				yaml_response += serialize_url_map_info(request, item, "yaml")
			if yaml_response == "":
				raise Http404
			response = StreamingHttpResponse(yaml_response, content_type="text/plain")
			response['Access-Control-Allow-Origin'] = '*'
			return response
		else:
			json_response = []
			for item in mapObject:
				json_response.append(serialize_url_map_info(request, item))
			if len(json_response) == 0:
				raise Http404
			response = StreamingHttpResponse(json.dumps(json_response), content_type="application/javascript")
			response['Access-Control-Allow-Origin'] = '*'
			return response
	
	# get minimap preview by hash (represented in JSON by encoded into base64)
	elif arg == "minimap":
		map_hashes = arg1.split(',')
		mapObject = Maps.objects.filter(map_hash__in=map_hashes)
		if not mapObject:
			raise Http404
		if arg2 == "yaml":
			yaml_response = ""
			for item in mapObject:
				yaml_response += serialize_minimap_map_info(request, item, "yaml")
			if yaml_response == "":
				raise Http404
			response = StreamingHttpResponse(yaml_response, content_type="text/plain")
			response['Access-Control-Allow-Origin'] = '*'
			return response
		else:
			json_response = []
			for item in mapObject:
				json_response.append(serialize_minimap_map_info(request, item))
			if len(json_response) == 0:
				raise Http404
			response = StreamingHttpResponse(json.dumps(json_response), content_type="application/javascript")
			response['Access-Control-Allow-Origin'] = '*'
			return response
	
	# get detailed map info + encoded minimap + URL for a range of maps (supports filters)
	elif arg == "list":
		mod = arg1
		if mod == "":
			raise Http404
		if arg2 not in ["rating", "-rating", "players", "-players", "posted", "-posted", "author", "uploader"]:
			raise Http404
		try:
			mapObject = Maps.objects.filter(game_mod=mod.lower(),players__gte=1,requires_upgrade=False,downloading=True).distinct('map_hash')
			if arg2 == "players":
				mapObject = sorted(mapObject, key=lambda x: (x.players), reverse=True)
			if arg2 == "-players":
				mapObject = sorted(mapObject, key=lambda x: (x.players), reverse=False)
			if arg2 == "posted":
				mapObject = sorted(mapObject, key=lambda x: (x.posted), reverse=True)
			if arg2 == "-posted":
				mapObject = sorted(mapObject, key=lambda x: (x.posted), reverse=False)
			if arg2 == "rating":
				mapObject = sorted(mapObject, key=lambda x: (x.rating_score), reverse=True)
			if arg2 == "-rating":
				mapObject = sorted(mapObject, key=lambda x: (x.rating_score), reverse=False)
			if arg2 == "author":
				if arg3 == "":
					mapObject = []
				else:
					if arg3 != "yaml":
						mapObject = mapObject.filter(author__iexact=arg3.lower())
						if not mapObject:
							mapObject = []
					else:
						mapObject = []
			if arg2 == "uploader":
				if arg3 == "":
					mapObject = []
				else:
					if arg3 != "yaml":
						try:
							u = User.objects.get(username__iexact=arg3.lower())
							mapObject = mapObject.filter(user_id=u.id)
						except:
							mapObject = []
					else:
						mapObject = []
		except:
			raise Http404
		page = 1
		try:
			page = int(arg3)
		except:
			pass
		perPage = 24
		slice_start = perPage*int(page)-perPage
		slice_end = perPage*int(page)
		mapObject = mapObject[slice_start:slice_end]
		if "yaml" in [arg3, arg4]:
			yaml_response = ""
			for item in mapObject:
				yaml_response += serialize_basic_map_info(request, item, "yaml")
			response = StreamingHttpResponse(yaml_response, content_type="text/plain")
			response['Access-Control-Allow-Origin'] = '*'
			return response
		else:
			json_response = []
			for item in mapObject:
				response_data = serialize_basic_map_info(request, item)
				json_response.append(response_data)
			response = StreamingHttpResponse(json.dumps(json_response), content_type="application/javascript")
			response['Access-Control-Allow-Origin'] = '*'
			return response

	elif arg == "sync":
		mod = arg1
		if mod == "":
			raise Http404
		try:
			mapObject = Maps.objects.filter(game_mod=mod.lower()).filter(next_rev=0,players__gte=1)
			mapObject = mapObject.filter(requires_upgrade=False).filter(downloading=True).distinct("map_hash")
			mapObject = sorted(mapObject, key=lambda x: (x.id))
			if not mapObject:
				raise Http404
		except:
			raise Http404
		data = ""
		for item in mapObject:
			data = data + get_url(request, item.id) + "/sync" + "\n"
		response = StreamingHttpResponse(data, content_type="plain/text")
		response['Access-Control-Allow-Origin'] = '*'
		return response
	elif arg == "syncall":
		mod = arg1
		if mod == "":
			raise Http404
		mapObject = Maps.objects.filter(game_mod=mod.lower(),players__gte=1).distinct("map_hash")
		mapObject = sorted(mapObject, key=lambda x: (x.id))
		if not mapObject:
			raise Http404
		data = ""
		for item in mapObject:
			data = data + get_url(request, item.id) + "/sync" + "\n"
		response = StreamingHttpResponse(data, content_type="plain/text")
		response['Access-Control-Allow-Origin'] = '*'
		return response
	else:
		# serve application/zip by hash
		oramap = ""
		try:
			mapObject = Maps.objects.get(map_hash=arg)
		except:
			raise Http404
		if not mapObject.downloading:
			raise Http404
		path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/maps/' + str(mapObject.id)
		try:
			mapDir = os.listdir(path)
		except:
			raise Http404
		for filename in mapDir:
			if filename.endswith(".oramap"):
				oramap = filename
				break
		if oramap == "":
			raise Http404
		serveOramap = path + os.sep + oramap
		oramap = os.path.splitext(oramap)[0] + "-" + str(mapObject.revision) + ".oramap"
		response = StreamingHttpResponse(open(serveOramap), content_type='application/zip')
		response['Content-Disposition'] = 'attachment; filename = %s' % oramap
		response['Content-Length'] = os.path.getsize(serveOramap)
		Maps.objects.filter(id=mapObject.id).update(downloaded=mapObject.downloaded+1)
		return response

def serialize_minimap_map_info(request, mapObject, yaml=""):
	minimap = get_minimap(mapObject.id)
	url = get_url(request, mapObject.id)

	last_revision = True
	if mapObject.next_rev != 0:
		last_revision = False
	if yaml:
		response_data = """{0}:
		id: {1}
		minimap: {2}
		spawnpoints: {3}
		url: {4}
		revision: {5}
		last_revision: {6}\n""".format(
		mapObject.map_hash,
		mapObject.id,
		minimap,
		mapObject.spawnpoints,
		url,
		mapObject.revision,
		last_revision,
		).replace("\t\t","\t")
		return response_data
	response_data = {}
	response_data['id'] = mapObject.id
	response_data['minimap'] = minimap
	response_data['spawnpoints'] = mapObject.spawnpoints
	response_data['url'] = url
	response_data['map_hash'] = mapObject.map_hash
	response_data['revision'] = mapObject.revision
	response_data['last_revision'] = last_revision
	return response_data

def serialize_url_map_info(request, mapObject, yaml=""):
	url = get_url(request, mapObject.id)
	last_revision = True
	if mapObject.next_rev != 0:
		last_revision = False
	if yaml:
		response_data = """{0}:
		id: {1}
		url: {2}
		revision: {3}
		last_revision: {4}\n""".format(
		mapObject.map_hash,
		mapObject.id,
		url,
		mapObject.revision,
		last_revision,
		).replace("\t\t","\t")
		return response_data
	response_data = {}
	response_data['id'] = mapObject.id
	response_data['url'] = url
	response_data['map_hash'] = mapObject.map_hash
	response_data['revision'] = mapObject.revision
	response_data['last_revision'] = last_revision
	return response_data

def serialize_basic_map_info(request, mapObject, yaml=""):
	minimap = get_minimap(mapObject.id, True)
	url = get_url(request, mapObject.id)
	last_revision = True
	if mapObject.next_rev != 0:
		last_revision = False
	license, icons = misc.selectLicenceInfo(mapObject)
	if license != None:
		license = "Creative Commons " + license
	else:
		license = "null"
	if yaml:
		response_data = """{0}:
		id: {1}
		title: {2}
		description: {3}
		info: {4}
		author: {5}
		map_type: {6}
		players: {7}
		game_mod: {8}
		width: {9}
		height: {10}
		bounds: {11}
		spawnpoints: {12}
		tileset: {13}
		revision: {14}
		last_revision: {15}
		requires_upgrade: {16}
		advanced_map: {17}
		lua: {18}
		posted: {19}
		viewed: {20}
		downloaded: {21}
		rating_votes: {22}
		rating_score: {23}
		license: {24}
		minimap: {25}
		url: {26}
		downloading: {27}\n""".format(
		mapObject.map_hash,
		mapObject.id,
		mapObject.title,
		mapObject.description,
		mapObject.info,
		mapObject.author,
		mapObject.map_type,
		mapObject.players,
		mapObject.game_mod,
		mapObject.width,
		mapObject.height,
		mapObject.bounds,
		mapObject.spawnpoints,
		mapObject.tileset,
		mapObject.revision,
		last_revision,
		mapObject.requires_upgrade,
		mapObject.advanced_map,
		mapObject.lua,
		str(mapObject.posted),
		mapObject.viewed,
		mapObject.downloaded,
		mapObject.rating_votes,
		mapObject.rating_score,
		license,
		minimap,
		url,
		mapObject.downloading,
		).replace("\t\t","\t")
		return response_data
	response_data = {}
	response_data['id'] = mapObject.id
	response_data['title'] = mapObject.title
	response_data['description'] = mapObject.description
	response_data['info'] = mapObject.info
	response_data['author'] = mapObject.author
	response_data['map_type'] = mapObject.map_type
	response_data['players'] = mapObject.players
	response_data['game_mod'] = mapObject.game_mod
	response_data['map_hash'] = mapObject.map_hash
	response_data['width'] = mapObject.width
	response_data['height'] = mapObject.height
	response_data['bounds'] = mapObject.bounds
	response_data['spawnpoints'] = mapObject.spawnpoints
	response_data['tileset'] = mapObject.tileset
	response_data['revision'] = mapObject.revision
	response_data['last_revision'] = last_revision
	response_data['requires_upgrade'] = mapObject.requires_upgrade
	response_data['advanced_map'] = mapObject.advanced_map
	response_data['lua'] = mapObject.lua
	response_data['posted'] = str(mapObject.posted)
	response_data['viewed'] = mapObject.viewed
	response_data['downloaded'] = mapObject.downloaded
	response_data['rating_votes'] = mapObject.rating_votes
	response_data['rating_score'] = mapObject.rating_score
	response_data['license'] = license
	response_data['minimap'] = minimap
	response_data['url'] = url
	response_data['downloading'] = mapObject.downloading
	return response_data

def get_minimap(mapid, soft=False):
	minimap = ""
	path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/maps/' + str(mapid)
	try:
		mapDir = os.listdir(path)
	except:
		if soft:
			return ""
		else:
			raise Http404
	for filename in mapDir:
		if filename.endswith("-mini.png"):
			minimap = filename
			break
	if minimap == "":
		if soft:
			return ""
		else:
			raise Http404
	with open(path + os.sep + minimap, "rb") as image_file:
		minimap = base64.b64encode(image_file.read())
	return minimap

def get_url(request, mapid):
	url = "http://" + request.META['HTTP_HOST'] + "/maps/" + str(mapid) + "/oramap"
	return url

# Crash Log API
@csrf_exempt
def CrashLogs(request):
	ID = 0
	gameID = 0
	desync = False
	if request.method != 'POST':
		return HttpResponseRedirect('https://github.com/ihptru/OpenRA/issues')

	if not request.POST.get('gameID', False):
		raise Http404
	if not request.POST.get('description', False):
		raise Http404
	gameID = request.POST.get('gameID', False)
	description = request.POST.get('description', False)

	if request.POST.get('desync', False):
		temp = request.POST.get('desync', False)
		if temp == 'True':
			desync = True

	try:
		openraLogs = request.FILES['logs']
	except:
		raise Http404

	transac = CrashReports(
		gameID = int(gameID),
		description = description,
		isdesync = desync,
		gistID = 0,
		)
	transac.save()
	ID = transac.id

	path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/crashlogs/' + str(ID) + os.sep
	if not os.path.exists(path):
		os.makedirs(path)

	z = zipfile.ZipFile(openraLogs, mode='a')
	z.extractall(path)
	z.close()

	resp = description + "\n"
	logfiles = os.listdir(path)
	for filename in logfiles:
		if filename in ['.','..']:
			continue
		resp += "http://" + request.META['HTTP_HOST'] + "/crashlogs/" + str(ID) + os.sep + os.path.splitext(filename)[0] + "\n"

	# perform Gist manipulatons if it's a desync
	if desync:
		crashObject = CrashReports.objects.filter(gameID=int(gameID))
		if len(crashObject) == 1:
			with open(path + "syncreport.log", "r") as syncContent:
				fileToGist = syncContent.read()
			if len(fileToGist) == 0:
				fileToGist = "empty syncreport"
			gistContent = {}
			gistContent['description'] = "desync GameID:"+gameID
			gistContent['public'] = True
			gistContent['files'] = {"GameID:"+gameID:{"content":fileToGist}}
			gistContent = json.dumps(gistContent)
			command = "curl -k -X POST --data '%s' https://api.github.com/gists?access_token=%s > /dev/null 2>&1" % (gistContent, settings.GITHUB_API_TOKEN)
			os.system(command)
			stream = urllib2.urlopen("https://api.github.com/gists?access_token=%s" % settings.GITHUB_API_TOKEN).read().decode()
			stream = json.loads(stream)
			foundGIST = 0
			for item in stream:
				if item['description'] == "desync GameID:"+gameID:
					foundGIST = item['id']
					break
			if foundGIST != 0:
				CrashReports.objects.filter(id=ID).update(gistID=int(foundGIST))
			resp = resp + "\nSyncreport Gist:\nhttps://gist.github.com/%s/%s/revisions" % (settings.GITHUB_USER, foundGIST)
		else:
			gistID = str(crashObject[0].gistID)
			CrashReports.objects.filter(id=ID).update(gistID=gistID)
			with open(path + "syncreport.log", "r") as syncContent:
				fileToGist = syncContent.read()
			gistContent = {}
			gistContent['description'] = "desync GameID:"+gameID
			gistContent['files'] = {"GameID:"+gameID:{"content":fileToGist}}
			gistContent = json.dumps(gistContent)
			command = "curl -k -X PATCH --data '%s' https://api.github.com/gists/%s?access_token=%s > /dev/null 2>&1" % (gistContent, gistID, settings.GITHUB_API_TOKEN)
			os.system(command)
			resp = resp + "\nSyncreport Gist:\nhttps://gist.github.com/%s/%s/revisions" % (settings.GITHUB_USER, gistID)

	# create a new issue at github repository with info about OpenRA crash report or append to an existing issue with the same gameID
	stream = urllib2.urlopen('https://api.github.com/repos/%s/%s/issues' % (settings.GITHUB_USER, settings.GITHUB_REPO)).read().decode()
	stream = json.loads(stream)
	foundID = 0
	for item in stream:
		if item['title'] == "GameID:" + gameID:
			foundID = item['number']
			break
	if foundID != 0:
		content = {}
		content['body'] = resp
		content = json.dumps(content)
		command = "curl -k -X POST --data '%s' https://api.github.com/repos/%s/%s/issues/%s/comments?access_token=%s > /dev/null 2>&1" % (content, settings.GITHUB_USER, settings.GITHUB_REPO, foundID, settings.GITHUB_API_TOKEN)
		os.system(command)
	else:
		content = {}
		content['title'] = "GameID:" + gameID
		content['body'] = resp
		content = json.dumps(content)
		command = "curl -k -X POST --data '%s' https://api.github.com/repos/%s/%s/issues?access_token=%s > /dev/null 2>&1" % (content, settings.GITHUB_USER, settings.GITHUB_REPO, settings.GITHUB_API_TOKEN)
		os.system(command)
	return StreamingHttpResponse('Done, check https://github.com/%s/%s/search?q=GameID:%s&ref=cmdform&type=Issues\n' % (settings.GITHUB_USER, settings.GITHUB_REPO, gameID))

def CrashLogsServe(request, crashid, logfile):
	logfilename = ""
	path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/crashlogs/' + crashid.lstrip('0')
	try:
		Dir = os.listdir(path)
	except:
		return HttpResponseRedirect("/")
	for filename in Dir:
		if logfile in filename:
			logfilename = filename
			break
	if logfilename == "":
		return HttpResponseRedirect('/crashlogs/')
	serveLog = path + os.sep + logfilename
	response = StreamingHttpResponse(open(serveLog), content_type='plain/text')
	response['Content-Disposition'] = 'attachment; filename="%s"' % crashid.lstrip('0')+logfilename
	return response