from django.http import HttpResponse
from django.template import RequestContext, loader
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect

from .forms import UploadMapForm, AuthenticationForm
from openraData import handlers

def index(request):
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'index_content.html',
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
        'authenticationStatusMessage': authenticationStatusMessage, 
        'form': form,
    })
    return HttpResponse(template.render(context))

def logoutView(request):
    if request.user.is_authenticated():
        logout(request)
    return HttpResponseRedirect('/')

def ControlPanel(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login/')
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'control_panel.html',
    })
    return HttpResponse(template.render(context))

def maps(request):
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'maps.html',
    })
    return HttpResponse(template.render(context))

def units(request):
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'units.html',
    })
    return HttpResponse(template.render(context))

def mods(request):
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'mods.html',
    })
    return HttpResponse(template.render(context))

def uploadMap(request):
    uploadingLog = ""
    if request.method == 'POST':
        form = UploadMapForm(request.POST, request.FILES)
        if form.is_valid():
            uploadingMap = handlers.MapHandlers()
            uploadingMap.ProcessUploading(request.FILES['file'])
            if uploadingMap.map_is_uploaded:
                uploadingLog = uploadingMap.LOG
                uid = uploadingMap.UID
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

    else:
        form = UploadMapForm()

    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'uploadMap.html',
        'form': form,
        'uploadingLog': uploadingLog,
    })
    return HttpResponse(template.render(context))

def uploadUnit(request):
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'uploadUnit.html',
    })
    return HttpResponse(template.render(context))

def uploadMod(request):
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'uploadMod.html',
    })
    return HttpResponse(template.render(context))

def uploadPalette(request):
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'uploadPalette.html',
    })
    return HttpResponse(template.render(context))