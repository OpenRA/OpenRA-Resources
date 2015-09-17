import os
import math
import re
import urllib2
import datetime
import shutil
import multiprocessing
import random
import operator
import json
import cgi
from django.conf import settings
from django.http import StreamingHttpResponse
from django.template import RequestContext, loader
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, Http404
from django.db import connection
from django.db.models import Count
from django.db.models import Max
from django.utils import timezone

from .forms import AddScreenshotForm
from django.db.models import F
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount
from threadedcomments.models import ThreadedComment
from openraData import handlers, misc, utility
from openraData.models import Maps, Lints, Screenshots, Reports, NotifyOfComments, ReadComments, UserOptions, Rating
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site

def index(request):
	scObject = Screenshots.objects.filter(ex_name="maps").order_by('-posted')[0:5]
	if request.user.id:
		newcomments = len(ReadComments.objects.filter(owner=request.user.id))
	else:
		newcomments = False
	template = loader.get_template('index.html')
	template_args = {
		'content': 'index_content.html',
		'request': request,
		'http_host': request.META['HTTP_HOST'],
		'title': '',
		'screenshots': scObject,
		'newcomments': newcomments,
	}
	if settings.SITE_MAINTENANCE:
		template_args['content'] = 'service/maintenance.html'
		template_args['maintenance_over'] = settings.SITE_MAINTENANCE_OVER
	context = RequestContext(request, template_args)
	return StreamingHttpResponse(template.render(context))

def logoutView(request):
	if request.user.is_authenticated():
		logout(request)
	return HttpResponseRedirect('/')

def feed(request):
	mapObject = Maps.objects.order_by("-posted")[0:20]
	d = datetime.datetime.utcnow()
	lastBuildDate = d.isoformat("T")
	template = loader.get_template('feed.html')
	context = RequestContext(request, {
		'request': request,
		'http_host': request.META['HTTP_HOST'],
		'title': 'OpenRA Resource Center - RSS Feed',
		'lastBuildDate': lastBuildDate,
		'mapObject': mapObject,
	})
	return StreamingHttpResponse(template.render(context), content_type='text/xml')

def search(request):
	if request.method == 'POST':
		if request.POST.get('qsearch', "").strip() == "":
			return HttpResponseRedirect('/')
		search_request = request.POST.get('qsearch', "").strip()
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

	template = loader.get_template('index.html')
	context = RequestContext(request, {
		'content': 'search.html',
		'request': request,
		'http_host': request.META['HTTP_HOST'],
		'title': ' - Search',
		'global_search_request': global_search_request,
		'search_request': search_request,
	})
	return StreamingHttpResponse(template.render(context))

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

	comments = misc.count_comments_for_many(mapObject, 'map')

	template = loader.get_template('index.html')
	context = RequestContext(request, {
		'content': 'control_panel.html',
		'request': request,
		'http_host': request.META['HTTP_HOST'],
		'title': ' - My Content',
		'maps': mapObject,
		'page': int(page),
		'range': [i+1 for i in range(rowsRange)],
		'amount_maps': amount,
		'comments': comments,
	})
	return StreamingHttpResponse(template.render(context))

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

	comments = misc.count_comments_for_many(mapObject, 'map')

	template = loader.get_template('index.html')
	template_args = {
		'content': 'maps.html',
		'request': request,
		'http_host': request.META['HTTP_HOST'],
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

	context = RequestContext(request, template_args)
	return StreamingHttpResponse(template.render(context))

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

	comments = misc.count_comments_for_many(mapObject, 'map')

	template = loader.get_template('index.html')
	context = RequestContext(request, {
		'content': 'mapsFromAuthor.html',
		'request': request,
		'http_host': request.META['HTTP_HOST'],
		'title': ' - Maps From ' + author,
		'maps': mapObject,
		'page': int(page),
		'range': [i+1 for i in range(rowsRange)],
		'amount': amount,
		'author': author,
		'comments': comments,
	})
	return StreamingHttpResponse(template.render(context))

def randomMap(request):
	mapObject = Maps.objects.filter(next_rev=0).distinct('map_hash')
	mapObject = random.choice(mapObject)
	return HttpResponseRedirect('/maps/'+str(mapObject.id))

def mostRatedMap(request):
	max_rating = Maps.objects.all().aggregate(Max('rating'))['rating__max']
	voteObject = Maps.objects.filter(rating=max_rating)
	voteObject = random.choice(voteObject)
	return HttpResponseRedirect('/maps/'+str(voteObject.id))

def mostCommentedMap(request):
	mapObject = Maps.objects.filter(next_rev=0)
	comments = misc.count_comments_for_many(mapObject, 'map')
	mapid = max(comments.iteritems(), key=operator.itemgetter(1))[0]
	return HttpResponseRedirect('/maps/'+mapid)

def mostViewedMap(request):
	max_viewed = Maps.objects.all().aggregate(Max('viewed'))['viewed__max']
	mapObject = Maps.objects.filter(viewed=max_viewed)
	mapObject = random.choice(mapObject)
	return HttpResponseRedirect('/maps/'+str(mapObject.id))

def mostDownloadedMap(request):
	max_downloaded = Maps.objects.all().aggregate(Max('downloaded'))['downloaded__max']
	mapObject = Maps.objects.filter(downloaded=max_downloaded)
	mapObject = random.choice(mapObject)
	return HttpResponseRedirect('/maps/'+str(mapObject.id))

def activelyDevelopedMap(request):
	max_developed = Maps.objects.all().aggregate(Max('revision'))['revision__max']
	mapObject = Maps.objects.filter(revision=max_developed)
	mapObject = random.choice(mapObject)
	return HttpResponseRedirect('/maps/'+str(mapObject.id))

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
		elif request.POST.get('comment', "") != "" and request.POST.get('name', "") != "":
			content_type = ContentType.objects.filter(name='Map')[0]
			userObject = User.objects.filter(pk=request.user.id)
			if not userObject:
				userObject = None
			else:
				userObject = userObject[0]
			if request.POST.get('email', "") != "":
				email = request.POST['email']
			else:
				email = ""
			transac = ThreadedComment(
				content_type = content_type,
				object_pk = int(request.POST['object_pk']),
				user = userObject,
				user_name = request.POST['name'],
				user_email = email,
				user_url = '',
				comment = request.POST['comment'].strip(),
				title = request.POST['title'],
				submit_date = timezone.now(),
				is_public = True,
				is_removed = False,
				site_id = 1,
			)
			transac.save()
			comment_id = transac.id
			mapObj = Maps.objects.get(id=arg)
			if request.user.id:
				userID = request.user.id
			else:
				userID = 0
			ntfObj = NotifyOfComments.objects.filter(object_type='map',object_id=arg).exclude(user=userID).exclude(user=mapObj.user_id)
			for item in ntfObj:
				singleUserOptions = UserOptions.objects.filter(user=item.user_id)
				mail_addr = misc.return_email(item.user_id)
				if not singleUserOptions:
					transac_uo = UserOptions(
						user = User.objects.get(pk=item.user_id),
						notifications_email = True,
						notifications_site = True,
					)
					transac_uo.save()
					transac_rc = ReadComments(
						owner = User.objects.get(pk=mapObj.user_id),
						object_type = 'map',
						object_id = arg,
						comment_id = comment_id,
						ifread = False,
					)
					transac_rc.save()
					if mail_addr:
						misc.send_email_to_user_OnComment('map', arg, mail_addr)
				else:
					if singleUserOptions[0].notifications_email:
						if mail_addr:
							misc.send_email_to_user_OnComment('map', arg, mail_addr)
					if singleUserOptions[0].notifications_site:
						transac_rc = ReadComments(
							owner = User.objects.get(pk=mapObj.user_id),
							object_type = 'map',
							object_id = arg,
							comment_id = comment_id,
							ifread = False,
						)
						transac_rc.save()
			if not ntfObj:
				transac_rc = ReadComments(
					owner = User.objects.get(pk=mapObj.user_id),
					object_type = 'map',
					object_id = arg,
					comment_id = comment_id,
					ifread = False,
				)
				transac_rc.save()
			ntfObj = NotifyOfComments.objects.filter(object_type='map',object_id=arg,user=userID)
			if not ntfObj:
				if userID != 0: # not anonymous
					transac_noc = NotifyOfComments(
						user = User.objects.get(pk=userID),
						object_type = 'map',
						object_id = arg,
					)
					transac_noc.save()
			if mapObj.user_id != userID:
				sOC = UserOptions.objects.filter(user=mapObj.user_id)
				mail_addr = misc.return_email(mapObj.user_id)
				if mail_addr:
					if sOC:
						if sOC[0].notifications_email:
							misc.send_email_to_user_OnComment('map', arg, mail_addr, 'owner')
					else:
						transac_uo = UserOptions(
							user = User.objects.get(pk=mapObj.user_id),
							notifications_email = True,
							notifications_site = True,
						)
						transac_uo.save()
						misc.send_email_to_user_OnComment('map', arg, mail_addr, 'owner')
			return HttpResponseRedirect('/maps/'+arg)
	fullPreview = False
	disk_size = 0
	path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/maps/' + arg
	try:
		mapDir = os.listdir(path)
		for filename in mapDir:
			if filename.endswith("-full.png"):
				fullPreview = True
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
		mapsFromAuthor = random.sample(mapsFromAuthor, 8)
	else:
		mapsFromAuthor = random.sample(mapsFromAuthor, len(mapsFromAuthor))

	similarMaps = Maps.objects.filter(next_rev=0,game_mod=mapObject.game_mod,tileset=mapObject.tileset,players=mapObject.players,map_type=mapObject.map_type,width=mapObject.width,height=mapObject.height).exclude(map_hash=mapObject.map_hash)[0:8]

	duplicates = Maps.objects.filter(map_hash=mapObject.map_hash).exclude(id=mapObject.id)
	if duplicates:
		duplicates = True

	screenshots = Screenshots.objects.filter(ex_name="maps",ex_id=arg)

	played_counter = urllib2.urlopen("http://master.openra.net/map_stats?hash=%s" % mapObject.map_hash).read().decode()
	played_counter = json.loads(played_counter)
	if played_counter:
		played_counter = played_counter["played"]
	else:
		played_counter = 0

	ratesAmount = Rating.objects.filter(ex_id=mapObject.id,ex_name='map')
	ratesAmount = len(ratesAmount)

	license, icons = misc.selectLicenceInfo(mapObject)
	userObject = User.objects.get(pk=mapObject.user_id)
	Maps.objects.filter(id=mapObject.id).update(viewed=mapObject.viewed+1)
	template = loader.get_template('index.html')
	context = RequestContext(request, {
		'content': 'displayMap.html',
		'request': request,
		'http_host': request.META['HTTP_HOST'],
		'title': ' - Map details - ' + mapObject.title,
		'map': mapObject,
		'userid': userObject,
		'arg': arg,
		'fullPreview': fullPreview,
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
	})
	return StreamingHttpResponse(template.render(context))

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
			return HttpResponseRedirect("/"+name+"/"+arg)
	return HttpResponseRedirect("/")

def deleteComment(request, arg, itemname, itemid):
	comObject = ThreadedComment.objects.filter(id=arg)
	if comObject:
		if comObject[0].user == request.user or request.user.is_superuser:
			comObject[0].delete()
	return HttpResponseRedirect("/"+itemname+"/"+itemid)

def serveScreenshot(request, itemid, itemname=""):
	image = ""
	path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/screenshots/' + itemid
	Dir = os.listdir(path)
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
	response = StreamingHttpResponse(open(image), content_type='image/'+mime)
	response['Content-Disposition'] = 'attachment; filename = %s' % fn
	return response

def serveRender(request, arg):
	render = ""
	path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/maps/' + arg
	try:
		mapDir = os.listdir(path)
	except:
		return HttpResponseRedirect("/")
	for filename in mapDir:
		if filename.endswith("-full.png"):
			render = filename
			break
	if render == "":
		return HttpResponseRedirect('/maps/'+arg)
	else:
		serveImage = path + os.sep + render
		response = StreamingHttpResponse(open(serveImage), content_type='image/png')
		response['Content-Disposition'] = 'attachment; filename = %s' % render
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
	response = StreamingHttpResponse(open(serveImage), content_type='image/png')
	response['Content-Disposition'] = 'attachment; filename = %s' % minimap
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
		response = StreamingHttpResponse(open(serveOramap), content_type='application/zip')
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
	response = StreamingHttpResponse(open(path+fname), content_type='image/gif')
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
		'http_host': request.META['HTTP_HOST'],
		'title': ' - Uploading Map',
		'uid': uid,
		'previous_rev': previous_rev,
		'previous_rev_title': previous_rev_title,
		'parsers': list(reversed( settings.OPENRA_VERSIONS.values() )),
		'bleed_tag': bleed_tag,
		'error_response': error_response,
	}

	if settings.SITE_MAINTENANCE:
		template_args['content'] = 'service/maintenance.html'
		template_args['maintenance_over'] = settings.SITE_MAINTENANCE_OVER

	context = RequestContext(request, template_args)
	return StreamingHttpResponse(template.render(context))

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
		Lints.objects.filter(map_id=mapObject.id, item_type='maps').delete()
		ThreadedComment.objects.filter(object_pk=mapObject.id, title='map').delete()
		if mapObject.pre_rev != 0:
			Maps.objects.filter(id=mapObject.pre_rev).update(next_rev=mapObject.next_rev)
		if mapObject.next_rev != 0:
			Maps.objects.filter(id=mapObject.next_rev).update(pre_rev=mapObject.pre_rev)
		mapObject.delete()
	template = loader.get_template('index.html')
	context = RequestContext(request, {
		'content': 'deleteMap.html',
		'request': request,
		'http_host': request.META['HTTP_HOST'],
		'title': 'Delete Map',
		'mapTitle': mapTitle,
		'mapAuthor': mapAuthor,
	})
	return StreamingHttpResponse(template.render(context))

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
		'http_host': request.META['HTTP_HOST'],
		'title': ' - Uploading Replay',
		'response': response,
		'parsers': list(reversed( settings.OPENRA_VERSIONS.values() )),
		'bleed_tag': bleed_tag,
	}

	if settings.SITE_MAINTENANCE:
		template_args['content'] = 'service/maintenance.html'
		template_args['maintenance_over'] = settings.SITE_MAINTENANCE_OVER

	context = RequestContext(request, template_args)
	return StreamingHttpResponse(template.render(context))

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
	context = RequestContext(request, {
		'request': request,
		'http_host': request.META['HTTP_HOST'],
		'arg': arg,
		'form': form,
	})
	return StreamingHttpResponse(template.render(context))

def MapRevisions(request, arg, page=1):
	perPage = 20
	slice_start = perPage*int(page)-perPage
	slice_end = perPage*int(page)
	revs = misc.Revisions('map')
	revisions = revs.GetRevisions(arg)
	mapObject = Maps.objects.filter(id__in=revisions).order_by('-posted')
	amount = len(mapObject)
	rowsRange = int(math.ceil(amount/float(perPage)))   # amount of rows
	mapObject = mapObject[slice_start:slice_end]
	if len(mapObject) == 0 and int(page) != 1:
		return HttpResponseRedirect("/maps/%s/revisions/" % arg)

	comments = misc.count_comments_for_many(mapObject, 'map')

	template = loader.get_template('index.html')
	context = RequestContext(request, {
		'content': 'revisionsMap.html',
		'request': request,
		'http_host': request.META['HTTP_HOST'],
		'title': ' - Revisions',
		'maps': mapObject,
		'page': int(page),
		'range': [i+1 for i in range(rowsRange)],
		'amount': amount,
		'arg': arg,
		'comments': comments,
	})
	return StreamingHttpResponse(template.render(context))

def cancelReport(request, name, arg):
	if not request.user.is_authenticated:
		return HttpResponseRedirect('/')
	Reports.objects.filter(user_id=request.user.id, ex_id=arg, ex_name=name).delete()
	return HttpResponseRedirect('/'+name+'/'+arg)

def units(request):
	template = loader.get_template('index.html')
	context = RequestContext(request, {
		'content': 'units.html',
		'request': request,
		'http_host': request.META['HTTP_HOST'],
		'title': ' - Units',
	})
	return StreamingHttpResponse(template.render(context))

def mods(request):
	template = loader.get_template('index.html')
	context = RequestContext(request, {
		'content': 'mods.html',
		'request': request,
		'http_host': request.META['HTTP_HOST'],
		'title': ' - Mods',
	})
	return StreamingHttpResponse(template.render(context))

def palettes(request):
	template = loader.get_template('index.html')
	context = RequestContext(request, {
		'content': 'palettes.html',
		'request': request,
		'http_host': request.META['HTTP_HOST'],
		'title': ' - Palettes',
	})
	return StreamingHttpResponse(template.render(context))

def screenshots(request):
	template = loader.get_template('index.html')
	context = RequestContext(request, {
		'content': 'screenshots.html',
		'request': request,
		'http_host': request.META['HTTP_HOST'],
		'title': ' - Screenshots',
	})
	return StreamingHttpResponse(template.render(context))

def assets(request):
	noErrors = False
	mirrors_list = []
	url = 'http://open-ra.org/packages/'
	try:
		data = urllib2.urlopen(url).read()
		data = data.split('Parent Directory</a>')[1].split('<hr />')[0]
		mirrors = re.findall('<a href="(.*)">', data)
		for mirror in mirrors:
			links_list = []
			name = os.path.splitext(mirror)[0].replace('-',' ')
			links = urllib2.urlopen(url + mirror).read()
			links = links.split('\n')[0:-1]
			for onelink in links:
				try:
					status = urllib2.urlopen(onelink)
					status = "online"
				except HTTPError as e:
					status = "offline"
				links_list.append([onelink, status])
			mirrors_list.append([name, links_list])
			noErrors = True
	except:
		pass
	template = loader.get_template('index.html')
	context = RequestContext(request, {
		'content': 'assets.html',
		'request': request,
		'http_host': request.META['HTTP_HOST'],
		'title': ' - Assets Packages Mirrors',
		'noerrors': noErrors,
		'mirrors_list': mirrors_list,
	})
	return StreamingHttpResponse(template.render(context))

def replays(request):
	template = loader.get_template('index.html')
	context = RequestContext(request, {
		'content': 'replays.html',
		'request': request,
		'http_host': request.META['HTTP_HOST'],
		'title': ' - Replays',
	})
	return StreamingHttpResponse(template.render(context))

def uploadUnit(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/units/')
	template = loader.get_template('index.html')
	context = RequestContext(request, {
		'content': 'uploadUnit.html',
		'request': request,
		'http_host': request.META['HTTP_HOST'],
		'title': ' - Uploading Unit',
	})
	return StreamingHttpResponse(template.render(context))

def uploadMod(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/mods/')
	template = loader.get_template('index.html')
	context = RequestContext(request, {
		'content': 'uploadMod.html',
		'request': request,
		'http_host': request.META['HTTP_HOST'],
		'title': ' - Uploading Mod',
	})
	return StreamingHttpResponse(template.render(context))

def uploadPalette(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/palettes/')
	template = loader.get_template('index.html')
	context = RequestContext(request, {
		'content': 'uploadPalette.html',
		'request': request,
		'http_host': request.META['HTTP_HOST'],
		'title': ' - Uploading Palette',
	})
	return StreamingHttpResponse(template.render(context))

def handle404(request):
	template = loader.get_template('index.html')
	context = RequestContext(request, {
		'content': '404.html',
		'request': request,
		'http_host': request.META['HTTP_HOST'],
		'title': ' - Page not found',
	})
	return StreamingHttpResponse(template.render(context))

def profile(request):
	if request.user.id:
		newcomments = len(ReadComments.objects.filter(owner=request.user.id))
	else:
		newcomments = False
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/')
	mapObject = Maps.objects.filter(user_id=request.user.id,next_rev=0)
	amountMaps = len(mapObject)
	ifsocial = False
	social = SocialAccount.objects.filter(user=request.user.id)
	if len(social) != 0:
		ifsocial = True
	template = loader.get_template('index.html')
	context = RequestContext(request, {
		'content': 'profile.html',
		'request': request,
		'http_host': request.META['HTTP_HOST'],
		'title': ' - Profile',
		'amountMaps': amountMaps,
		'ifsocial': ifsocial,
		'newcomments': newcomments,
	})
	return StreamingHttpResponse(template.render(context))

def faq(request):
	template = loader.get_template('index.html')
	context = RequestContext(request, {
		'content': 'faq.html',
		'request': request,
		'http_host': request.META['HTTP_HOST'],
		'title': ' - FAQ',
	})
	return StreamingHttpResponse(template.render(context))

def links(request):
	template = loader.get_template('index.html')
	context = RequestContext(request, {
		'content': 'links.html',
		'request': request,
		'http_host': request.META['HTTP_HOST'],
		'title': ' - Links',
	})
	return StreamingHttpResponse(template.render(context))

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
	context = RequestContext(request, {
		'content': 'contacts.html',
		'request': request,
		'http_host': request.META['HTTP_HOST'],
		'title': ' - Contacts',
		'message_sent': message_sent,
	})
	return StreamingHttpResponse(template.render(context))

def contacts_sent(request):
	message_sent = True
	template = loader.get_template('index.html')
	context = RequestContext(request, {
		'content': 'contacts.html',
		'request': request,
		'http_host': request.META['HTTP_HOST'],
		'title': ' - Contacts',
		'message_sent': message_sent,
	})
	return StreamingHttpResponse(template.render(context))