from django.http import HttpResponse
from django.template import RequestContext, loader
#from django.http import HttpResponseRedirect
#from django.conf import settings

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
    if request.method == 'POST':
        form = UploadMapForm(request.POST, request.FILES)
        if form.is_valid():
            handlers.handle_uploaded_map(request.FILES['file'])
            #return HttpResponseRedirect('/maps/')
    else:
        form = UploadMapForm()

    template = loader.get_template('index.html')
    context = RequestContext(request, {
        'content': 'maps.html',
        'form': form,
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
