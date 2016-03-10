import os
import math
import re
import urllib.request
import datetime
import shutil
import random
import operator
import json
import cgi
from django.conf import settings
from django.http import StreamingHttpResponse
from django.template import RequestContext, loader
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, Http404
from django.db.models import Max
from django.utils import timezone

from .forms import AddScreenshotForm
from django.db.models import F
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount
from openra import handlers, misc, utility
from openra.models import Maps, Replays, ReplayPlayers, Lints, Screenshots, Reports, Rating, Comments, UnsubscribeComments



def index(request):
	scObject = Screenshots.objects.filter(ex_name="maps").order_by('-posted')[0:5]

	template = loader.get_template('index.html')
	template_args = {
		'content': 'index_content.html',
		'request': request,
		'title': '',
		'screenshots': scObject,
	}
	if settings.SITE_MAINTENANCE:
		template_args['content'] = 'service/maintenance.html'
		template_args['maintenance_over'] = settings.SITE_MAINTENANCE_OVER
	return StreamingHttpResponse(template.render(template_args, request))



def loginView(request):
	template = loader.get_template('auth/login.html')
	template_args = {
		'request': request,
		'title': 'OpenRA Resource Center - Sign In',
	}
	return StreamingHttpResponse(template.render(template_args, request))



def logoutView(request):

	if not request.user.is_authenticated():
		return HttpResponseRedirect('/')

	if request.method == "POST":
		logout(request)
		return HttpResponseRedirect('/')

	template = loader.get_template('auth/logout.html')
	template_args = {
		'request': request,
		'title': 'OpenRA Resource Center - Sign Out',
	}
	return StreamingHttpResponse(template.render(template_args, request))



def feed(request):
	mapObject = Maps.objects.order_by("-posted")[0:20]
	d = datetime.datetime.utcnow()
	lastBuildDate = d.isoformat("T")
	template = loader.get_template('feed.html')
	template_args = {
		'request': request,
		'title': 'OpenRA Resource Center - RSS Feed',
		'lastBuildDate': lastBuildDate,
		'mapObject': mapObject,
	}
	return StreamingHttpResponse(template.render(template_args, request), content_type='text/xml')



def search(request, arg=""):

	if not arg:
		if request.method == 'POST':
			if request.POST.get('qsearch', "").strip() == "":
				return HttpResponseRedirect('/')
			return HttpResponseRedirect('/search/' + request.POST.get('qsearch', "").strip() )
		else:
			return HttpResponseRedirect('/')

	search_request = arg

	global_search_request = {}
	global_search_request['maps'] = {'amount': 0, 'hash': None, 'title': None, 'info': None}

	s_by_hash = Maps.objects.filter(map_hash=search_request)
	global_search_request['maps']['hash'] = s_by_hash
	global_search_request['maps']['amount'] += len(s_by_hash)

	s_by_title = Maps.objects.filter(title__icontains=search_request)
	global_search_request['maps']['title'] = s_by_title
	global_search_request['maps']['amount'] += len(s_by_title)

	s_by_info = Maps.objects.filter(info__icontains=search_request)
	global_search_request['maps']['amount'] += len(s_by_info)

	s_by_description = Maps.objects.filter(description__icontains=search_request).exclude(info__icontains=search_request)
	global_search_request['maps']['amount'] += len(s_by_description)
	global_search_request['maps']['info'] = [s_by_info, s_by_description]

	s_by_author = Maps.objects.filter(author__icontains=search_request)
	global_search_request['maps']['author'] = s_by_author
	global_search_request['maps']['amount'] += len(s_by_author)

	template = loader.get_template('index.html')
	template_args = {
		'content': 'search.html',
		'request': request,
		'title': ' - Search',
		'global_search_request': global_search_request,
		'search_request': search_request,
	}
	return StreamingHttpResponse(template.render(template_args, request))



def ControlPanel(request, page=1, filter=""):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/login/')
	perPage = 16
	slice_start = perPage*int(page)-perPage
	slice_end = perPage*int(page)
	mapObject = Maps.objects.filter(user_id=request.user.id).filter(next_rev=0).order_by('-posted')
	amount = len(mapObject)
	rowsRange = int(math.ceil(amount/float(perPage)))   # amount of rows
	mapObject = mapObject[slice_start:slice_end]
	if len(mapObject) == 0 and int(page) != 1:
		return HttpResponseRedirect("/panel/")

	comments = misc.count_comments_for_many(mapObject, 'maps')

	template = loader.get_template('index.html')
	template_args = {
		'content': 'control_panel.html',
		'request': request,
		'title': ' - My Content',
		'maps': mapObject,
		'page': int(page),
		'range': [i+1 for i in range(rowsRange)],
		'amount_maps': amount,
		'comments': comments,
	}
	return StreamingHttpResponse(template.render(template_args, request))

def maps(request, page=1, filter=""):
	perPage = 20
	slice_start = perPage*int(page)-perPage
	slice_end = perPage*int(page)
	mapObject = Maps.objects.filter(next_rev=0).distinct('map_hash').order_by('map_hash', '-posted')
	mapObject = sorted(mapObject, key=lambda x: (x.posted), reverse=True)
	amount = len(mapObject)
	rowsRange = int(math.ceil(amount/float(perPage)))   # amount of rows
	mapObject = mapObject[slice_start:slice_end]
	amount_this_page = len(mapObject)
	if amount_this_page == 0 and int(page) != 1:
		return HttpResponseRedirect("/maps/")

	comments = misc.count_comments_for_many(mapObject, 'maps')

	template = loader.get_template('index.html')
	template_args = {
		'content': 'maps.html',
		'request': request,
		'title': ' - Maps',
		'maps': mapObject,
		'page': int(page),
		'range': [i+1 for i in range(rowsRange)],
		'amount': amount,
		'comments': comments,
	}

	if settings.SITE_MAINTENANCE:
		template_args['content'] = 'service/maintenance.html'
		template_args['maintenance_over'] = settings.SITE_MAINTENANCE_OVER

	return StreamingHttpResponse(template.render(template_args, request))



def mapsFromAuthor(request, author, page=1):
	perPage = 20
	slice_start = perPage*int(page)-perPage
	slice_end = perPage*int(page)
	mapObject = Maps.objects.filter(next_rev=0, author=author.replace("%20", " ")).distinct('map_hash').order_by('map_hash', '-posted')
	mapObject = sorted(mapObject, key=lambda x: (x.posted), reverse=True)
	amount = len(mapObject)
	rowsRange = int(math.ceil(amount/float(perPage)))   # amount of rows
	mapObject = mapObject[slice_start:slice_end]
	if len(mapObject) == 0 and int(page) != 1:
		return HttpResponseRedirect("/maps/author/%s/" % author)

	comments = misc.count_comments_for_many(mapObject, 'maps')

	template = loader.get_template('index.html')
	template_args = {
		'content': 'mapsFromAuthor.html',
		'request': request,
		'title': ' - Maps From ' + author,
		'maps': mapObject,
		'page': int(page),
		'range': [i+1 for i in range(rowsRange)],
		'amount': amount,
		'author': author,
		'comments': comments,
	}
	return StreamingHttpResponse(template.render(template_args, request))



def randomMap(request):
	mapObject = Maps.objects.filter(next_rev=0).distinct('map_hash')
	mapObject = random.choice(mapObject)
	return HttpResponseRedirect('/maps/'+str(mapObject.id)+'/')



def mostRatedMap(request):
	max_rating = Maps.objects.all().aggregate(Max('rating'))['rating__max']
	voteObject = Maps.objects.filter(rating=max_rating)
	voteObject = random.choice(voteObject)
	return HttpResponseRedirect('/maps/'+str(voteObject.id)+'/')



def mostCommentedMap(request):
	mapObject = Maps.objects.filter(next_rev=0)
	comments = misc.count_comments_for_many(mapObject, 'maps')
	mapid = max(comments.items(), key=operator.itemgetter(1))[0]
	return HttpResponseRedirect('/maps/'+mapid+'/')



def mostViewedMap(request):
	max_viewed = Maps.objects.all().aggregate(Max('viewed'))['viewed__max']
	mapObject = Maps.objects.filter(viewed=max_viewed)
	mapObject = random.choice(mapObject)
	return HttpResponseRedirect('/maps/'+str(mapObject.id)+'/')



def mostDownloadedMap(request):
	max_downloaded = Maps.objects.all().aggregate(Max('downloaded'))['downloaded__max']
	mapObject = Maps.objects.filter(downloaded=max_downloaded)
	mapObject = random.choice(mapObject)
	return HttpResponseRedirect('/maps/'+str(mapObject.id)+'/')



def activelyDevelopedMap(request):
	max_developed = Maps.objects.all().aggregate(Max('revision'))['revision__max']
	mapObject = Maps.objects.filter(revision=max_developed)
	mapObject = random.choice(mapObject)
	return HttpResponseRedirect('/maps/'+str(mapObject.id)+'/')



def displayReplay(request, arg):
	try:
		orarepObj = Replays.objects.get(id=arg)
	except:
		return HttpResponseRedirect('/')

	path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/replays/' + arg
	disk_size = os.path.getsize(path + '/' + arg + '.orarep')
	disk_size = misc.sizeof_fmt(disk_size)

	reportedByUser = False
	reports = []
	reportObject = Reports.objects.filter(ex_id=orarepObj.id, ex_name='replays')
	for item in reportObject:
		reports.append([item.user.username, item.reason, item.infringement, item.posted])
		if item.user_id == request.user.id:
			reportedByUser = True

	template = loader.get_template('index.html')
	template_args = {
		'content': 'displayReplay.html',
		'request': request,
		'title': ' - Replay details - ' + arg,
		'orarep': orarepObj,
		'reports': reports,
		'reported': reportedByUser,
		'screenshots': 0,
		'disk_size': disk_size,
		'duplicates': 0,
	}
	return StreamingHttpResponse(template.render(template_args, request))



def displayMap(request, arg):
	if request.method == 'POST':
		if request.POST.get('reportReason', "").strip() != "":
			checkReports = Reports.objects.filter(user_id=request.user.id, ex_id=arg, ex_name='maps')
			if not checkReports:
				checkReports = Reports.objects.filter(ex_id=arg, ex_name='maps')
				infringement = request.POST.get('infringement', False)
				if infringement == "true":
					infringement = True
				transac = Reports(
					user_id = request.user.id,
					reason = request.POST['reportReason'].strip(),
					ex_id = arg,
					ex_name = 'maps',
					infringement = infringement,
					posted = timezone.now(),
				)
				transac.save()
				Maps.objects.filter(id=arg).update(amount_reports=F('amount_reports')+1)
				misc.send_email_to_admin_OnReport({'addr':request.META['HTTP_HOST']+'/maps/'+arg, 'user_id':request.user.id, 'reason':request.POST['reportReason'].strip(), 'infringement':infringement,})
				misc.send_email_to_user_OnReport({'addr':request.META['HTTP_HOST']+'/maps/'+arg, 'owner_id':Maps.objects.get(id=arg).user_id, 'reason':request.POST['reportReason'].strip(), 'resource_type':'map',})
				return HttpResponseRedirect('/maps/'+arg)
		elif request.POST.get('mapInfo', False) != False:
			if request.user.is_superuser:
				Maps.objects.filter(id=arg).update(info=request.POST['mapInfo'].strip())
			else:
				Maps.objects.filter(id=arg, user_id=request.user.id).update(info=request.POST['mapInfo'].strip())
			return HttpResponseRedirect('/maps/'+arg)
		elif request.FILES.get('scfile', False) != False:
			form = AddScreenshotForm(request.POST, request.FILES)
			if form.is_valid():
				handlers.addScreenshot(request.FILES['scfile'], arg, request.user, 'map')
		elif request.POST.get('comment', "") != "":
			transac = Comments(
				item_type = 'maps',
				item_id = int(arg),
				user = request.user,
				content = request.POST['comment'].strip(),
				posted = timezone.now(),
				is_removed = False,
			)
			transac.save()

			commented_map_obj = Maps.objects.get(id=arg)
			if commented_map_obj.user != request.user:
				misc.send_email_to_user_OnComment('maps', arg, commented_map_obj.user.email, info="owner")

			comsObj = Comments.objects.filter(item_type='maps', item_id=arg, is_removed=False)
			if comsObj:
				for com in comsObj:
					if com.user != request.user and com.user != commented_map_obj.user:

						unsubObj = UnsubscribeComments.objects.filter(item_type='maps', item_id=arg, user=com.user)

						if not unsubObj:
							misc.send_email_to_user_OnComment('maps', arg, com.user.email)

			return HttpResponseRedirect('/maps/' + arg + '/')

	disk_size = 0
	path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/maps/' + arg
	try:
		mapDir = os.listdir(path)
		for filename in mapDir:
			if filename.endswith(".oramap"):
				disk_size = os.path.getsize(path + '/' + filename)
				disk_size = misc.sizeof_fmt(disk_size)
	except:
		pass
	try:
		mapObject = Maps.objects.get(id=arg)
	except:
		return HttpResponseRedirect('/')

	lints = []
	lintObject = Lints.objects.filter(map_id=mapObject.id, item_type='maps')
	lintObject = sorted(lintObject, key=lambda x: (x.posted), reverse=False)
	for lint_item in lintObject:
		lints.append([lint_item.version_tag, lint_item.pass_status, lint_item.lint_output])

	reportedByUser = False
	reports = []
	reportObject = Reports.objects.filter(ex_id=mapObject.id, ex_name='maps')
	for item in reportObject:
		try:
			usr = User.objects.get(pk=item.user_id)
			reports.append([usr.username, item.reason, item.infringement, item.posted])
		except:
			pass
		if item.user_id == request.user.id:
			reportedByUser = True

	luaNames = []
	listContent = os.listdir(path + '/content/')
	for fn in listContent:
		if fn.endswith('.lua'):
			luaNames.append(os.path.splitext(fn)[0])

	shpNames = []
	listContent = os.listdir(path + '/content/')
	for fn in listContent:
		if fn.endswith('.shp.gif'):
			shpNames.append(fn.split('.shp.gif')[0])

	mapsFromAuthor = Maps.objects.filter(author=mapObject.author,next_rev=0).exclude(id=mapObject.id).distinct('map_hash').order_by('map_hash', '-posted').exclude(map_hash=mapObject.map_hash)
	if len(mapsFromAuthor) >= 8:
		mapsFromAuthor = random.sample(list(mapsFromAuthor), 8)
	else:
		mapsFromAuthor = random.sample(list(mapsFromAuthor), len(mapsFromAuthor))

	similarMaps = Maps.objects.filter(next_rev=0,game_mod=mapObject.game_mod,tileset=mapObject.tileset,players=mapObject.players,map_type=mapObject.map_type,width=mapObject.width,height=mapObject.height).exclude(map_hash=mapObject.map_hash)[0:8]

	duplicates = Maps.objects.filter(map_hash=mapObject.map_hash).exclude(id=mapObject.id)
	if duplicates:
		duplicates = True

	screenshots = Screenshots.objects.filter(ex_name="maps",ex_id=arg)

	played_counter = urllib.request.urlopen("http://master.openra.net/map_stats?hash=%s" % mapObject.map_hash).read().decode()
	played_counter = json.loads(played_counter)
	if played_counter:
		played_counter = played_counter["played"]
	else:
		played_counter = 0

	ratesAmount = Rating.objects.filter(ex_id=mapObject.id,ex_name='map')
	ratesAmount = len(ratesAmount)

	comments = misc.get_comments_for_all_revisions(request, 'maps', arg)

	license, icons = misc.selectLicenceInfo(mapObject)
	userObject = User.objects.get(pk=mapObject.user_id)
	Maps.objects.filter(id=mapObject.id).update(viewed=mapObject.viewed+1)
	template = loader.get_template('index.html')
	template_args = {
		'content': 'displayMap.html',
		'request': request,
		'title': ' - Map details - ' + mapObject.title,
		'map': mapObject,
		'userid': userObject,
		'arg': arg,
		'license': license,
		'icons': icons,
		'reports': reports,
		'reported': reportedByUser,
		'luaNames': luaNames,
		'mapsFromAuthor': mapsFromAuthor,
		'similarMaps': similarMaps,
		'screenshots': screenshots,
		'shpNames': shpNames,
		'disk_size': disk_size,
		'duplicates': duplicates,
		'played_counter': played_counter,
		'ratesAmount': ratesAmount,
		'REPORTS_PENALTY_AMOUNT': settings.REPORTS_PENALTY_AMOUNT,
		'lints': lints,
		'comments': comments,
	}
	return StreamingHttpResponse(template.render(template_args, request))



def deleteScreenshot(request, itemid):
	scObject = Screenshots.objects.filter(id=itemid)
	if scObject:
		arg = str(scObject[0].ex_id)
		name = scObject[0].ex_name
		if request.user.is_superuser or scObject[0].user_id == request.user.id:
			path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/screenshots/' + itemid
			try:
				shutil.rmtree(path)
			except:
				pass
			scObject[0].delete()
			return HttpResponseRedirect("/"+name+"/"+arg+"/")
	return HttpResponseRedirect("/")



def deleteComment(request, arg, item_type, item_id):
	comObject = Comments.objects.filter(id=arg)
	if comObject:
		if comObject[0].user == request.user or request.user.is_superuser:
			Comments.objects.filter(id=arg).update(is_removed=True)

			coms_exist_for_map_for_user = Comments.objects.filter(id=arg, is_removed=False, user=request.user.id)
			if not coms_exist_for_map_for_user:
				UnsubscribeComments.objects.filter(item_type=item_type, item_id=item_id, user=request.user.id).delete()

	return HttpResponseRedirect("/"+item_type+"/"+item_id+"/")



def unsubscribe_from_comments(request, item_type, arg):
	if request.user.is_authenticated:
		unsubObj = UnsubscribeComments.objects.filter(user=request.user.id)
		if not unsubObj:
			transac = UnsubscribeComments(
				user = request.user,
				item_type = item_type,
				item_id = arg,
				unsubscribed = timezone.now(),
			)
			transac.save()
		else:
			unsubObj.delete()

	return HttpResponseRedirect("/" + item_type + "/" + arg + "/")



def serveScreenshot(request, itemid, itemname=""):
	image = ""
	path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/screenshots/' + itemid
	try:
		Dir = os.listdir(path)
	except:
		return HttpResponseRedirect("/")
	for fn in Dir:
		if "-mini." in fn:
			if itemname == "mini":
				image = path + "/" + fn
				mime = fn.split('.')[1]
				break
		else:
			if itemname == "":
				image = path + "/" + fn
				mime = fn.split('.')[1]
				break
	if image == "":
		return StreamingHttpResponse("")
	response = StreamingHttpResponse(open(image, 'rb'), content_type='image/'+mime)
	response['Content-Disposition'] = 'attachment; filename = %s' % fn
	return response



def serveMinimap(request, arg):
	minimap = ""
	path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/maps/' + arg
	try:
		mapDir = os.listdir(path)
	except:
		return HttpResponseRedirect("/")
	for filename in mapDir:
		if filename.endswith("-mini.png"):
			minimap = filename
			serveImage = path + os.sep + minimap
			break
	contentDir = os.listdir(path + '/content/')
	for filename in contentDir:
		if filename == "map.png":
			minimap = filename
			serveImage = path + '/content/' + minimap
			break
	if minimap == "":
		minimap = "nominimap.png"
		serveImage = os.getcwd() + os.sep + __name__.split('.')[0] + '/static/images/nominimap.png'
	response = StreamingHttpResponse(open(serveImage, 'rb'), content_type='image/png')
	response['Content-Disposition'] = 'attachment; filename = %s' % minimap
	return response



def serveReplay(request, arg):
	orarep = ""
	path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/replays/' + arg + '/' + arg + '.orarep'
	if not os.path.isfile(path):
		return HttpResponseRedirect('/replays/'+arg)

	response = StreamingHttpResponse(open(path, 'rb'), content_type='application/octet-stream')
	response['Content-Disposition'] = 'attachment; filename = %s' % arg+'.orarep'
	response['Content-Length'] = os.path.getsize(path)
	Replays.objects.filter(id=arg).update(downloaded=F('downloaded')+1)
	return response



def serveOramap(request, arg, sync=""):
	oramap = ""
	path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/maps/' + arg
	try:
		mapDir = os.listdir(path)
	except:
		return HttpResponseRedirect("/")
	for filename in mapDir:
		if filename.endswith(".oramap"):
			oramap = filename
			break
	if oramap == "":
		return HttpResponseRedirect('/maps/'+arg)
	else:
		serveOramap = path + os.sep + oramap
		if sync == "sync":
				oramap = arg + ".oramap"
		response = StreamingHttpResponse(open(serveOramap, 'rb'), content_type='application/zip')
		response['Content-Disposition'] = 'attachment; filename = %s' % oramap
		response['Content-Length'] = os.path.getsize(serveOramap)
		Maps.objects.filter(id=arg).update(downloaded=F('downloaded')+1)
		return response



def serveYaml(request, arg):
	path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/maps/' + arg + os.sep + '/content/map.yaml'
	response = StreamingHttpResponse(cgi.escape(open(path).read(), quote=None), content_type='application/plain')
	response['Content-Disposition'] = 'attachment; filename = map.yaml'
	return response



def serveYamlRules(request, arg):
	path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/maps/' + arg + os.sep + '/content/map.yaml'
	result = ""
	start = False
	fn = open(path, 'r')
	lines = fn.readlines()
	fn.close()
	for line in lines:
		if "Rules:" in line:
			start = True
		if start:
			result += line
	response = StreamingHttpResponse(cgi.escape(result, quote=None), content_type='application/plain')
	response['Content-Disposition'] = 'attachment; filename = advanced.%s' % arg
	return response



def serveLua(request, arg, name):
	path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/maps/' + arg + os.sep + '/content/'
	fname = ""
	listdir = os.listdir(path)
	for fn in listdir:
		if fn.endswith('.lua'):
			if os.path.splitext(fn)[0] == name:
				fname = fn
				break
	if fname == "":
		raise Http404
	response = StreamingHttpResponse(cgi.escape(open(path+fname).read(), quote=None), content_type='application/plain')
	response['Content-Disposition'] = 'attachment; filename = %s' % fname
	return response



def serveMapSHP(request, arg, name, request_type='preview'):
	path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/maps/' + arg + '/content/'
	fname = ""
	listdir = os.listdir(path)
	for fn in listdir:
		if request_type == 'preview':
			if fn.endswith('.shp.gif'):
				if fn.split('.shp.gif')[0] == name:
					fname = fn
					break
		elif request_type == 'fetch':
			if fn.endswith('.shp'):
				if fn.split('.shp')[0] == name:
					fname = fn
					break
	if fname == "":
		raise Http404
	response = StreamingHttpResponse(open(path+fname, 'rb'), content_type='image/gif')
	response['Content-Disposition'] = 'attachment; filename = %s' % fname
	return response



def uploadMap(request, previous_rev=0):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/maps/')
	error_response = False
	uid = False
	rev = 1
	previous_rev_title = ""
	user_id = request.user.id
	if previous_rev != 0:
		mapObject = Maps.objects.filter(id=previous_rev)
		if mapObject:
			rev = mapObject[0].revision + 1
			previous_rev_title = mapObject[0].title
			if request.user.is_superuser:
				user_id = mapObject[0].user_id
	if request.method == 'POST':
		if request.FILES.get('file', None) != None:
			uploadingMap = handlers.MapHandlers()
			error_response = uploadingMap.ProcessUploading(user_id, request.FILES['file'], request.POST, rev, previous_rev)
			if uploadingMap.UID:
				uid = str(uploadingMap.UID)
				if error_response == False:
					return HttpResponseRedirect('/maps/' + uid + "/")

	bleed_tag = None
	if (settings.OPENRA_BLEED_HASH_FILE_PATH != ''):
		bleed_tag = open(settings.OPENRA_BLEED_HASH_FILE_PATH, 'r')
		bleed_tag = 'git-' + bleed_tag.readline().strip()[0:7]

	template = loader.get_template('index.html')
	template_args = {
		'content': 'uploadMap.html',
		'request': request,
		'title': ' - Uploading Map',
		'uid': uid,
		'previous_rev': previous_rev,
		'previous_rev_title': previous_rev_title,
		'rev': rev,
		'parsers': list(reversed( list(settings.OPENRA_VERSIONS.values()) )),
		'bleed_tag': bleed_tag,
		'error_response': error_response,
	}

	if settings.SITE_MAINTENANCE:
		template_args['content'] = 'service/maintenance.html'
		template_args['maintenance_over'] = settings.SITE_MAINTENANCE_OVER

	return StreamingHttpResponse(template.render(template_args, request))



def DeleteMap(request, arg):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/maps/')
	try:
		mapObject = Maps.objects.get(id=arg)
	except:
		return HttpResponseRedirect('/maps/')
	mapTitle = mapObject.title
	mapAuthor = mapObject.author
	if mapObject.user_id == request.user.id or request.user.is_superuser:
		path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/maps/' + arg
		try:
			shutil.rmtree(path)
		except:
			pass
		Screenshots.objects.filter(ex_id=mapObject.id, ex_name='maps').delete()
		Reports.objects.filter(ex_id=mapObject.id, ex_name='maps').delete()
		Comments.objects.filter(item_id=mapObject.id, item_type='maps').delete()
		UnsubscribeComments.objects.filter(item_id=mapObject.id, item_type='maps').delete()
		Lints.objects.filter(map_id=mapObject.id, item_type='maps').delete()
		if mapObject.pre_rev != 0:
			Maps.objects.filter(id=mapObject.pre_rev).update(next_rev=mapObject.next_rev)
		if mapObject.next_rev != 0:
			Maps.objects.filter(id=mapObject.next_rev).update(pre_rev=mapObject.pre_rev)
		mapObject.delete()
	template = loader.get_template('index.html')
	template_args = {
		'content': 'deleteMap.html',
		'request': request,
		'title': 'Delete Map',
		'mapTitle': mapTitle,
		'mapAuthor': mapAuthor,
	}
	return StreamingHttpResponse(template.render(template_args, request))



def uploadReplay(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/replays/')
	response = {'error': False, 'response': ''}

	if request.method == 'POST':
		if request.FILES.get('replay_file', None) != None:

			replay_file = handlers.ReplayHandlers()
			response = replay_file.process_uploading(request.user.id, request.FILES['replay_file'], request.POST)
			if replay_file.UID:
				if response['error'] == False:
					return HttpResponseRedirect('/replays/' + str(replay_file.UID) + "/")

	bleed_tag = None
	if (settings.OPENRA_BLEED_HASH_FILE_PATH != ''):
		bleed_tag = open(settings.OPENRA_BLEED_HASH_FILE_PATH, 'r')
		bleed_tag = 'git-' + bleed_tag.readline().strip()[0:7]

	template = loader.get_template('index.html')
	template_args = {
		'content': 'uploadReplay.html',
		'request': request,
		'title': ' - Uploading Replay',
		'response': response,
		'parsers': list(reversed( list(settings.OPENRA_VERSIONS.values()) )),
		'bleed_tag': bleed_tag,
	}

	if settings.SITE_MAINTENANCE:
		template_args['content'] = 'service/maintenance.html'
		template_args['maintenance_over'] = settings.SITE_MAINTENANCE_OVER

	return StreamingHttpResponse(template.render(template_args, request))



def SetDownloadingStatus(request, arg):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/maps/'+arg)
	try:
		mapObject = Maps.objects.get(id=arg)
	except:
		return HttpResponseRedirect('/maps/')
	if mapObject.user_id == request.user.id or request.user.is_superuser:
		if mapObject.downloading:
			Maps.objects.filter(id=arg).update(downloading=False)
		else:
			Maps.objects.filter(id=arg).update(downloading=True)
	return HttpResponseRedirect('/maps/'+arg)



def ChangeRsyncStatus(request, arg):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/maps/'+arg)
	try:
		mapObject = Maps.objects.get(id=arg)
	except:
		return HttpResponseReirect('/maps/')
	if mapObject.user_id == request.user.id or request.user.is_superuser:
		if mapObject.rsync_allow:
			Maps.objects.filter(id=arg).update(rsync_allow=False)
		else:
			Maps.objects.filter(id=arg).update(rsync_allow=True)
	return HttpResponseRedirect('/maps/'+arg)



def addScreenshot(request, arg, item):
	if item == 'map':
		Object = Maps.objects.filter(id=arg)
	if not (Object[0].user_id == request.user.id or request.user.is_superuser):
		return StreamingHttpResponse("")
	form = AddScreenshotForm()
	template = loader.get_template('addScreenshotForm.html')
	template_args = {
		'request': request,
		'arg': arg,
		'form': form,
	}
	return StreamingHttpResponse(template.render(template_args, request))



def MapRevisions(request, arg, page=1):
	perPage = 20
	slice_start = perPage*int(page)-perPage
	slice_end = perPage*int(page)
	revs = misc.Revisions('maps')
	revisions = revs.GetRevisions(arg)
	mapObject = Maps.objects.filter(id__in=revisions).order_by('-revision', '-posted')
	amount = len(mapObject)
	rowsRange = int(math.ceil(amount/float(perPage)))   # amount of rows
	mapObject = mapObject[slice_start:slice_end]
	if len(mapObject) == 0 and int(page) != 1:
		return HttpResponseRedirect("/maps/%s/revisions/" % arg)

	comments = misc.count_comments_for_many(mapObject, 'maps')

	template = loader.get_template('index.html')
	template_args = {
		'content': 'revisionsMap.html',
		'request': request,
		'title': ' - Revisions',
		'maps': mapObject,
		'page': int(page),
		'range': [i+1 for i in range(rowsRange)],
		'amount': amount,
		'arg': arg,
		'comments': comments,
	}
	return StreamingHttpResponse(template.render(template_args, request))



def cancelReport(request, name, arg):
	if not request.user.is_authenticated:
		return HttpResponseRedirect('/')
	Reports.objects.filter(user_id=request.user.id, ex_id=arg, ex_name=name).delete()
	return HttpResponseRedirect('/'+name+'/'+arg)



def screenshots(request):
	template = loader.get_template('index.html')
	template_args = {
		'content': 'screenshots.html',
		'request': request,
		'title': ' - Screenshots',
	}
	return StreamingHttpResponse(template.render(template_args, request))



def comments(request, page=1):
	perPage = 20
	slice_start = perPage*int(page)-perPage
	slice_end = perPage*int(page)

	comments = Comments.objects.filter(is_removed=False).order_by('-posted')
	amount = len(comments)
	rowsRange = int(math.ceil(amount/float(perPage)))   # amount of rows
	comments = comments[slice_start:slice_end]
	amount_this_page = len(comments)

	if amount_this_page == 0 and int(page) != 1:
		return HttpResponseRedirect("/comments/")

	last_comment_id_seen = request.COOKIES.get('last_comment_id_seen', comments[0].id)

	template = loader.get_template('index.html')
	template_args = {
		'content': 'comments.html',
		'request': request,
		'title': ' - Comments',
		'comments': comments,
		'amount': amount,
		'amount_this_page': amount_this_page,
		'range': [i+1 for i in range(rowsRange)],
		'page': int(page),
		'last_comment_id_seen': int(last_comment_id_seen),
	}
	response = StreamingHttpResponse(template.render(template_args, request))
	if int(page) == 1:
		response.set_cookie('last_comment_id_seen', comments[0].id, max_age=4320000)
	return response



def comments_by_user(request, arg, page=1):
	perPage = 20
	slice_start = perPage*int(page)-perPage
	slice_end = perPage*int(page)

	comments = Comments.objects.filter(is_removed=False, user=arg).order_by('-posted')
	amount = len(comments)
	rowsRange = int(math.ceil(amount/float(perPage)))   # amount of rows
	comments = comments[slice_start:slice_end]
	amount_this_page = len(comments)

	if amount_this_page == 0 and int(page) != 1:
		return HttpResponseRedirect("/comments/user/"+arg+"/")

	template = loader.get_template('index.html')
	template_args = {
		'content': 'comments.html',
		'request': request,
		'title': ' - Comments by ' + request.user.username,
		'comments': comments,
		'amount': amount,
		'amount_this_page': amount_this_page,
		'range': [i+1 for i in range(rowsRange)],
		'page': int(page),
		'comments_by_user': True,
	}
	return StreamingHttpResponse(template.render(template_args, request))



def replays(request, page=1):
	perPage = 10
	slice_start = perPage*int(page)-perPage
	slice_end = perPage*int(page)
	replayObject = Replays.objects.filter().distinct('sha1sum').order_by('sha1sum', '-posted')
	replayObject = sorted(replayObject, key=lambda x: (x.posted), reverse=True)
	amount = len(replayObject)
	rowsRange = int(math.ceil(amount/float(perPage)))   # amount of rows
	replayObject = replayObject[slice_start:slice_end]
	amount_this_page = len(replayObject)
	if amount_this_page == 0 and int(page) != 1:
		return HttpResponseRedirect("/replays/")

	template = loader.get_template('index.html')
	template_args = {
		'content': 'replays.html',
		'request': request,
		'title': ' - Replays',
		'replays': replayObject,
		'page': int(page),
		'range': [i+1 for i in range(rowsRange)],
		'amount': amount,
	}

	if settings.SITE_MAINTENANCE:
		template_args['content'] = 'service/maintenance.html'
		template_args['maintenance_over'] = settings.SITE_MAINTENANCE_OVER

	return StreamingHttpResponse(template.render(template_args, request))



def handle404(request):
	template = loader.get_template('index.html')
	template_args = {
		'content': '404.html',
		'request': request,
		'title': ' - Page not found',
	}
	return StreamingHttpResponse(template.render(template_args, request), status=404)



def profile(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/')
	mapObject = Maps.objects.filter(user_id=request.user.id,next_rev=0)
	amountMaps = len(mapObject)
	ifsocial = False
	social = SocialAccount.objects.filter(user=request.user.id)
	if len(social) != 0:
		ifsocial = True
	template = loader.get_template('index.html')
	template_args = {
		'content': 'profile.html',
		'request': request,
		'title': ' - Profile',
		'amountMaps': amountMaps,
		'ifsocial': ifsocial,
	}
	return StreamingHttpResponse(template.render(template_args, request))



def faq(request):
	template = loader.get_template('index.html')
	template_args = {
		'content': 'faq.html',
		'request': request,
		'title': ' - FAQ',
	}
	return StreamingHttpResponse(template.render(template_args, request))



def links(request):
	template = loader.get_template('index.html')
	template_args = {
		'content': 'links.html',
		'request': request,
		'title': ' - Links',
	}
	return StreamingHttpResponse(template.render(template_args, request))



def contacts(request):
	message_sent = False
	if request.method == 'POST':
		if request.POST.get('contacts_submit', "").strip() != "":
			name = request.POST.get('name', "")
			email = request.POST.get('email', "")
			message = request.POST.get('message', "")
			misc.send_email_contacts_form(name, email, message)
			return HttpResponseRedirect('/contacts/sent/')
	template = loader.get_template('index.html')
	template_args = {
		'content': 'contacts.html',
		'request': request,
		'title': ' - Contacts',
		'message_sent': message_sent,
	}
	return StreamingHttpResponse(template.render(template_args, request))



def contacts_sent(request):
	message_sent = True
	template = loader.get_template('index.html')
	template_args = {
		'content': 'contacts.html',
		'request': request,
		'title': ' - Contacts',
		'message_sent': message_sent,
	}
	return StreamingHttpResponse(template.render(template_args, request))
