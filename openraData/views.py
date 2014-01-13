import os
from django.http import HttpResponse, StreamingHttpResponse
from django.template import RequestContext, loader
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect
from django.db import connection

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
        'title': ' - Login',
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

def maps(request):
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'maps.html',
        'request': request,
        'title': ' - Maps',
    })
    return HttpResponse(template.render(context))

def displayMap(request, arg):
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
    })
    return HttpResponse(template.render(context))

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
    response['Content-Disposition'] = 'attachment; filename="%s"' % minimap
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
        response['Content-Disposition'] = 'attachment; filename="%s"' % lintlog
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
        response['Content-Disposition'] = 'attachment; filename="%s"' % oramap
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
            if uploadingMap.map_is_uploaded:
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
        'title': ' - Uploading Map',
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
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'assets.html',
        'request': request,
        'title': ' - Assets Packages Mirrors',
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

def initMapProcedures(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/')
    if not request.user.is_superuser:
        return HttpResponseRedirect('/')
    functionInit = """
        DROP PROCEDURE IF EXISTS mapVersionsIDs;
        CREATE PROCEDURE mapVersionsIDs (IN mapid INT)
            BEGIN
            DECLARE save_id INT DEFAULT mapid;
            DECLARE p_list VARCHAR(1000) DEFAULT mapid;
            DECLARE n_list VARCHAR(1000) DEFAULT "";
            DECLARE amount INT DEFAULT 0;

            loop_n: WHILE TRUE DO
                SET amount = (SELECT COUNT(next_rev) FROM openraData_maps WHERE id = mapid);
                IF amount=0 THEN
                SELECT "" AS list;
                END IF;
                SET mapid=(SELECT next_rev FROM openraData_maps WHERE id = mapid);
                IF mapid=0 THEN
                LEAVE loop_n;
                END IF;
                SET n_list = CONCAT(n_list, ",", mapid);
            END WHILE;

            loop_p: WHILE TRUE DO
                SET amount = (SELECT COUNT(pre_rev) FROM openraData_maps WHERE id = save_id);
                IF amount=0 THEN
                SELECT "" AS list;
                END IF;
                SET save_id=(SELECT pre_rev FROM openraData_maps WHERE id = save_id);
                IF save_id=0 THEN
                LEAVE loop_p;
                END IF;
                SET p_list = CONCAT(save_id, ",", p_list);
            END WHILE;

            SET p_list = CONCAT(p_list, n_list);

            SELECT p_list AS list;
            END
        ;
    """
    cursor = connection.cursor()
    cursor.execute(functionInit)
    return HttpResponse("Created procedure 'mapVersionsIDs' successfully.")