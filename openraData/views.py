import os
import math
import re
import urllib2
import datetime
import shutil
import multiprocessing
import random
from django.conf import settings
from django.http import StreamingHttpResponse
from django.template import RequestContext, loader
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, Http404
from django.db import connection
from django.db.models import Count
from django.utils import timezone

from .forms import UploadMapForm
from .forms import AddScreenshotForm
from django.db.models import F
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount
from openraData import handlers, misc, triggers
from openraData.models import Maps, Screenshots, Comments, Reports

def index(request):
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'index_content.html',
        'request': request,
        'http_host': request.META['HTTP_HOST'],
        'title': '',
    })
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
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'search.html',
        'request': request,
        'http_host': request.META['HTTP_HOST'],
        'title': ' - Search',
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
    if len(mapObject) == 0 and int(page) != 1:
        return HttpResponseRedirect("/maps/")
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'maps.html',
        'request': request,
        'http_host': request.META['HTTP_HOST'],
        'title': ' - Maps',
        'maps': mapObject,
        'page': int(page),
        'range': [i+1 for i in range(rowsRange)],
        'amount': amount,
    })
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
    })
    return StreamingHttpResponse(template.render(context))

def displayMap(request, arg):
    if request.method == 'POST':
        if request.POST.get('reportReason', "").strip() != "":
            checkReports = Reports.objects.filter(user_id=request.user.id, ex_id=arg, ex_name='maps')
            if not checkReports:
                checkReports = Reports.objects.filter(ex_id=arg, ex_name='maps')
                if len(checkReports) >= 2:
                    Maps.objects.filter(id=arg).update(downloading=False)
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
                misc.send_email_to_admin_OnReport("Item: http://%s  By user_id: %s  Reason: %s  Infringement: %s" % (request.META['HTTP_HOST']+'/maps/'+arg, request.user.id, request.POST['reportReason'].strip(), infringement))
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
                handlers.addScreenshot(request.FILES['scfile'], arg, request.user.id, 'map')
    fullPreview = False
    path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/maps/' + arg
    try:
        mapDir = os.listdir(path)
        for filename in mapDir:
            if filename.endswith("-full.png"):
                fullPreview = True
                break
    except:
        pass
    try:
        mapObject = Maps.objects.get(id=arg)
    except:
        return HttpResponseRedirect('/')
    verpath = misc.addSlash(settings.OPENRA_PATH)
    versionFile = open(verpath + 'mods/ra/mod.yaml', 'r')
    version = versionFile.read()
    versionFile.close()
    try:
        version = re.findall('Version: (.*)', version)[0]
    except:
        version = "null"
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

    mapsFromAuthor = Maps.objects.filter(author=mapObject.author,next_rev=0).exclude(id=mapObject.id).distinct('map_hash').order_by('map_hash', '-posted').exclude(map_hash=mapObject.map_hash)
    if len(mapsFromAuthor) >= 6:
        mapsFromAuthor = random.sample(mapsFromAuthor, 6)
    else:
        mapsFromAuthor = random.sample(mapsFromAuthor, len(mapsFromAuthor))

    similarMaps = Maps.objects.filter(next_rev=0,game_mod=mapObject.game_mod,tileset=mapObject.tileset,players=mapObject.players,map_type=mapObject.map_type,width=mapObject.width,height=mapObject.height).exclude(id=mapObject.id)[0:6]
    
    screenshots = Screenshots.objects.filter(ex_name="maps",ex_id=arg)
    shp_previews = []

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
        'version': version,
        'reports': reports,
        'reported': reportedByUser,
        'luaNames': luaNames,
        'mapsFromAuthor': mapsFromAuthor,
        'similarMaps': similarMaps,
        'screenshots': screenshots,
        'shp_previews': shp_previews,
    })
    return StreamingHttpResponse(template.render(context))

def deleteScreenshot(request, arg, itemid):
    scObject = Screenshots.objects.filter(id=itemid)
    if scObject:
        if request.user.is_superuser or scObject[0].user_id == request.user.id:
            path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/screenshots/' + itemid
            try:
                shutil.rmtree(path)
            except:
                pass
            scObject[0].delete()
    return HttpResponseRedirect("/maps/"+arg+"/")

def serveScreenshot(request, arg, itemid, imgtype=""):
    image = ""
    path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/screenshots/' + itemid
    Dir = os.listdir(path)
    for fn in Dir:
        if fn.startswith(arg + "-mini."):
            if imgtype == "mini":
                image = path + "/" + fn
                mime = fn.split('.')[1]
                break
        else:
            if imgtype == "":
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
            break
    if minimap == "":
        minimap = "nominimap.png"
        serveImage = os.getcwd() + os.sep + __name__.split('.')[0] + '/static/images/nominimap.png'
    else:
        serveImage = path + os.sep + minimap
    response = StreamingHttpResponse(open(serveImage), content_type='image/png')
    response['Content-Disposition'] = 'attachment; filename = %s' % minimap
    return response

def serveLintLog(request, arg):
    lintlog = ""
    path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/maps/' + arg
    try:
        mapDir = os.listdir(path)
    except:
        return HttpResponseRedirect("/")
    for filename in mapDir:
        if filename == "lintlog":
            lintlog = filename
            break
    if lintlog == "":
        return HttpResponseRedirect('/maps/'+arg)
    else:
        serveLog = path + os.sep + lintlog
        response = StreamingHttpResponse(open(serveLog), content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename = %s' % lintlog
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
        Maps.objects.filter(id=arg).update(downloaded=F('downloaded')+1)
        return response

def serveYaml(request, arg):
    path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/maps/' + arg + os.sep + '/content/map.yaml'
    response = StreamingHttpResponse(open(path), content_type='application/plain')
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
    response = StreamingHttpResponse(result, content_type='application/plain')
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
    response = StreamingHttpResponse(open(path+fname), content_type='application/plain')
    response['Content-Disposition'] = 'attachment; filename = %s' % fname
    return response

def uploadMap(request, previous_rev=0):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/maps/')
    uploadingLog = []
    uid = False
    rev = 1
    previous_rev_title = ""
    if previous_rev != 0:
        mapObject = Maps.objects.filter(id=previous_rev)
        if mapObject:
            rev = mapObject[0].revision + 1
            previous_rev_title = mapObject[0].title
    initial = {'policy_cc': 'cc_yes', 'commercial': 'com_no', 'adaptations': 'adapt_alike'}
    if request.method == 'POST':
        form = UploadMapForm(request.POST, request.FILES, initial=initial)
        if form.is_valid():
            uploadingMap = handlers.MapHandlers()
            uploadingMap.ProcessUploading(request.user.id, request.FILES['file'], request.POST, rev, previous_rev)
            uploadingLog = uploadingMap.LOG
            if uploadingMap.UID:
                uid = str(uploadingMap.UID)
            form = UploadMapForm(initial=initial)
    else:
        form = UploadMapForm(initial=initial)

    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'uploadMap.html',
        'request': request,
        'http_host': request.META['HTTP_HOST'],
        'title': ' - Uploading Map',
        'form': form,
        'uploadingLog': uploadingLog,
        'uid': uid,
        'previous_rev': previous_rev,
        'previous_rev_title': previous_rev_title,
    })
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
        Comments.objects.filter(ex_id=mapObject.id, ex_name='maps').delete()
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

def addScreenshot(request, arg, item):
    if item == 'map':
        Object = Maps.objects.filter(id=arg)
    if Object[0].user_id != request.user.id:
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
    revs = handlers.Revisions('maps')
    revisions = revs.GetRevisions(arg)
    mapObject = Maps.objects.filter(id__in=revisions).order_by('-posted')
    amount = len(mapObject)
    rowsRange = int(math.ceil(amount/float(perPage)))   # amount of rows
    mapObject = mapObject[slice_start:slice_end]
    if len(mapObject) == 0 and int(page) != 1:
        return HttpResponseRedirect("/maps/%s/revisions/" % arg)
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

def uptime(request):
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'uptime.html',
        'request': request,
        'http_host': request.META['HTTP_HOST'],
        'title': ' - Uptime',
    })
    return StreamingHttpResponse(template.render(context))

def triggerLint(request):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/')
    mapObject = Maps.objects.all()
    amount = len(mapObject)
    p = multiprocessing.Process(target=triggers.LintCheck, args=(mapObject,), name='LintCheck')
    p.start()

    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'lintcheck.html',
        'request': request,
        'http_host': request.META['HTTP_HOST'],
        'title': ' - Lint Check',
        'amount': amount,
    })
    return StreamingHttpResponse(template.render(context))