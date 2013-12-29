import os
from django.http import HttpResponse, StreamingHttpResponse
from django.template import RequestContext, loader
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect

from .forms import UploadMapForm, AuthenticationForm
from django.contrib.auth.models import User
from openraData import handlers
from openraData.models import Maps

def index(request):
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'index_content.html',
        'request': request,
    })
    return HttpResponse(template.render(context))

def loginView(request):
    authenticationStatusMessage = ""
    if request.method == 'POST':
        form = AuthenticationForm(request.POST)
        if form.is_valid():
            if 'username' in request.POST and 'password' in request.POST:
                username = request.POST['username']
                password = request.POST['password']
                user = authenticate(username=username, password=password)
                if user is not None:
                    if user.is_active:
                        login(request, user)
                        return HttpResponseRedirect('/panel/')
                else:
                    authenticationStatusMessage = "Failed to authenticate"
    else:
        form = AuthenticationForm()

    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'login.html',
        'request': request,
        'authenticationStatusMessage': authenticationStatusMessage, 
        'form': form,
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
    })
    return HttpResponse(template.render(context))

def search(request):
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'search.html',
        'request': request,
    })
    return HttpResponse(template.render(context))

def ControlPanel(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login/')
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'control_panel.html',
        'request': request,
    })
    return HttpResponse(template.render(context))

def maps(request):
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'maps.html',
        'request': request,
    })
    return HttpResponse(template.render(context))

def displayMap(request, arg):
    try:
        mapObject = Maps.objects.get(id=arg.lstrip('0'))
    except:
        return HttpResponseRedirect('/')
    userObject = User.objects.get(pk=mapObject.user_id)
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'displayMap.html',
        'request': request,
        'map': mapObject,
        'userid': userObject,
        'arg': arg,
    })
    return HttpResponse(template.render(context))

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
    response = HttpResponse(open(serveImage), content_type='image/png')
    response['Content-Disposition'] = 'attachment; filename="%s"' % minimap
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
        response = HttpResponse(open(serveLog), content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="%s"' % lintlog
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
            if uploadingMap.map_is_uploaded:
                uid = str(uploadingMap.UID).rjust(7, '0')
                if uploadingMap.LintPassed:
                    pass
                else:
                    pass
                if uploadingMap.minimap_generated:
                    pass
                else:
                    pass
            else:
                pass
            form = UploadMapForm()

    else:
        form = UploadMapForm()

    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'uploadMap.html',
        'request': request,
        'form': form,
        'uploadingLog': uploadingLog,
        'uid': uid,
    })
    return HttpResponse(template.render(context))

def units(request):
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'units.html',
        'request': request,
    })
    return HttpResponse(template.render(context))

def mods(request):
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'mods.html',
        'request': request,
    })
    return HttpResponse(template.render(context))

def palettes(request):
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'palettes.html',
        'request': request,
    })
    return HttpResponse(template.render(context))

def uploadUnit(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/units/')
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'uploadUnit.html',
        'request': request,
    })
    return HttpResponse(template.render(context))

def uploadMod(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/mods/')
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'uploadMod.html',
        'request': request,
    })
    return HttpResponse(template.render(context))

def uploadPalette(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/palettes/')
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'uploadPalette.html',
        'request': request,
    })
    return HttpResponse(template.render(context))