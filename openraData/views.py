from django.http import HttpResponse
from django.template import RequestContext, loader
#from django.http import HttpResponseRedirect

from .forms import UploadMapForm
from openraData import handlers

def index(request):
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'index_content.html',
    })
    return HttpResponse(template.render(context))

def login(request):
    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'login.html',
    })
    return HttpResponse(template.render(context))

def maps(request):
    uploaded = False
    if request.method == 'POST':
        form = UploadMapForm(request.POST, request.FILES)
        if form.is_valid():
            uploadingMap = handlers.MapHandlers()
            uploadingMap.ProcessUploading(request.FILES['file'])
            if uploadingMap.map_is_uploaded:
                uploaded = True
            #return HttpResponseRedirect('/maps/')
    else:
        form = UploadMapForm()

    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'maps.html',
        'form': form,
        'uploaded': uploaded, 
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
