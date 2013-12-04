from django.http import HttpResponse
from django.conf import settings

def index(request):
    return HttpResponse("You are at the OpenRA Content Website index page.")

def mapAPI(request, arg, value=""):
    if arg == "title":
        pass
        # map info by title (title = value)
    elif arg == "hash":
        pass
        # map info by hash (hash = value)
    elif arg == "url":
        pass
        # map url by hash (hash = value)
    else:
        pass
        # download map by hash (hash = arg)
