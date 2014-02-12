import os
import math
import re
import urllib2
from django.http import HttpResponse, StreamingHttpResponse
from django.template import RequestContext, loader
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect
from django.db import connection
from django.db.models import Count

from .forms import UploadMapForm, AuthenticationForm
from django.contrib.auth.models import User
from openraData import handlers
from openraData.models import Maps

def index(request):
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'index_content.html',
        'request': request,
        'title': '',
    })
    return HttpResponse(template.render(context))

def logoutView(request):
    if request.user.is_authenticated():
        logout(request)
    return HttpResponseRedirect('/')

def feed(request):
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'feed.html',
        'request': request,
        'title': ' - Rss Feed',
    })
    return HttpResponse(template.render(context))

def search(request):
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'search.html',
        'request': request,
        'title': ' - Search',
    })
    return HttpResponse(template.render(context))

def ControlPanel(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login/')
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'control_panel.html',
        'request': request,
        'title': ' - My Content',
    })
    return HttpResponse(template.render(context))

def maps(request, page=1, filter=""):
    perPage = 36
    slice_start = perPage*int(page)-perPage
    slice_end = perPage*int(page)
    mapObject = Maps.objects.all().annotate(count_hashes=Count("map_hash")).order_by("-posted").filter(next_rev=0)
    amount = len(mapObject)
    rowsRange = int(math.ceil(amount/float(perPage)))
    mapObject = mapObject[slice_start:slice_end]
    if len(mapObject) == 0 and int(page) != 1:
        return HttpResponseRedirect("/maps/")
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'maps.html',
        'request': request,
        'title': ' - Maps',
        'maps': mapObject,
        'page': int(page),
        'range': [i+1 for i in range(rowsRange)],
        'amount': amount,
    })
    return HttpResponse(template.render(context))

def displayMap(request, arg):
    fullPreview = False
    path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/maps/' + arg.lstrip('0')
    try:
        mapDir = os.listdir(path)
        for filename in mapDir:
            if filename.endswith("-full.png"):
                fullPreview = True
                break
    except:
        pass
    try:
        mapObject = Maps.objects.get(id=arg.lstrip('0'))
    except:
        return HttpResponseRedirect('/')
    userObject = User.objects.get(pk=mapObject.user_id)
    Maps.objects.filter(id=mapObject.id).update(viewed=mapObject.viewed+1)
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'displayMap.html',
        'request': request,
        'title': ' - Map details - ' + mapObject.title,
        'map': mapObject,
        'userid': userObject,
        'arg': arg.lstrip('0'),
        'fullPreview': fullPreview,
    })
    return HttpResponse(template.render(context))

def serveRender(request, arg):
    render = ""
    path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/maps/' + arg.lstrip('0')
    try:
        mapDir = os.listdir(path)
    except:
        return HttpResponseRedirect("/")
    for filename in mapDir:
        if filename.endswith("-full.png"):
            render = filename
            break
    if render == "":
        return HttpResponseRedirect('/maps/'+arg.lstrip('0'))
    else:
        serveImage = path + os.sep + render
        response = HttpResponse(open(serveImage), content_type='image/png')
        response['Content-Disposition'] = 'attachment; filename = "%s"' % render
        return response

def serveMinimap(request, arg):
    minimap = ""
    path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/maps/' + arg.lstrip('0')
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
    response = HttpResponse(open(serveImage), content_type='image/png')
    response['Content-Disposition'] = 'attachment; filename = "%s"' % minimap
    return response

def serveLintLog(request, arg):
    lintlog = ""
    path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/maps/' + arg.lstrip('0')
    try:
        mapDir = os.listdir(path)
    except:
        return HttpResponseRedirect("/")
    for filename in mapDir:
        if filename == "lintlog":
            lintlog = filename
            break
    if lintlog == "":
        return HttpResponseRedirect('/maps/'+arg.lstrip('0'))
    else:
        serveLog = path + os.sep + lintlog
        response = HttpResponse(open(serveLog), content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename = "%s"' % lintlog
        return response

def serveOramap(request, arg, sync=""):
    oramap = ""
    path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/maps/' + arg.lstrip('0')
    try:
        mapDir = os.listdir(path)
    except:
        return HttpResponseRedirect("/")
    for filename in mapDir:
        if filename.endswith(".oramap"):
            oramap = filename
            break
    if oramap == "":
        return HttpResponseRedirect('/maps/'+arg.lstrip('0'))
    else:
        serveOramap = path + os.sep + oramap
        if sync == "sync":
                oramap = arg.lstrip('0') + ".oramap"
        response = HttpResponse(open(serveOramap), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename = "%s"' % oramap
        return response

def uploadMap(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/maps/')
    uploadingLog = []
    uid = False
    if request.method == 'POST':
        form = UploadMapForm(request.POST, request.FILES)
        if form.is_valid():
            uploadingMap = handlers.MapHandlers()
            uploadingMap.ProcessUploading(request.user.id, request.FILES['file'], request.POST['info'])
            uploadingLog = uploadingMap.LOG
            if uploadingMap.UID:
                uid = str(uploadingMap.UID)
            form = UploadMapForm()

    else:
        form = UploadMapForm()

    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'uploadMap.html',
        'request': request,
        'title': ' - Uploading Map',
        'form': form,
        'uploadingLog': uploadingLog,
        'uid': uid,
    })
    return StreamingHttpResponse(template.render(context))

def units(request):
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'units.html',
        'request': request,
        'title': ' - Units',
    })
    return HttpResponse(template.render(context))

def mods(request):
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'mods.html',
        'request': request,
        'title': ' - Mods',
    })
    return HttpResponse(template.render(context))

def palettes(request):
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'palettes.html',
        'request': request,
        'title': ' - Palettes',
    })
    return HttpResponse(template.render(context))

def screenshots(request):
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'screenshots.html',
        'request': request,
        'title': ' - Screenshots',
    })
    return HttpResponse(template.render(context))

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
        'title': ' - Assets Packages Mirrors',
        'noerrors': noErrors,
        'mirrors_list': mirrors_list,
    })
    return HttpResponse(template.render(context))

def replays(request):
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'replays.html',
        'request': request,
        'title': ' - Replays',
    })
    return HttpResponse(template.render(context))

def uploadUnit(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/units/')
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'uploadUnit.html',
        'request': request,
        'title': ' - Uploading Unit',
    })
    return HttpResponse(template.render(context))

def uploadMod(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/mods/')
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'uploadMod.html',
        'request': request,
        'title': ' - Uploading Mod',
    })
    return HttpResponse(template.render(context))

def uploadPalette(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/palettes/')
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'uploadPalette.html',
        'request': request,
        'title': ' - Uploading Palette',
    })
    return HttpResponse(template.render(context))

def handle404(request):
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': '404.html',
        'request': request,
        'title': ' - Page not found',
    })
    return HttpResponse(template.render(context))

def profile(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/')
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'profile.html',
        'request': request,
        'title': ' - Profile',
    })
    return HttpResponse(template.render(context))

def faq(request):
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'faq.html',
        'request': request,
        'title': ' - FAQ',
    })
    return HttpResponse(template.render(context))

def links(request):
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'links.html',
        'request': request,
        'title': ' - Links',
    })
    return HttpResponse(template.render(context))