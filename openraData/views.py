from django.http import HttpResponse
#from django.conf import settings

def index(request):
    return HttpResponse("You are at the OpenRA Content Website index page.")

# Map API

def mapAPI(request, arg, value="", filter=""):
    # get detailed map info by title
    if arg == "title":
        pass
        # map info by title (title = value)
    
    # get detailed map info by hash
    elif arg == "hash":
        pass
        # map info by hash (hash = value)
    
    # get URL of map by hash
    elif arg == "url":
        pass
        # map url by hash (hash = value)
    
    # get minimap preview by hash (represented in JSON by encoded into base64)
    elif arg == "minimap":
        pass
        # minimap.png for map in JSON format encoded into base64 (hash = value)
    
    # get detailed map info + encoded minimap + URL for a range of maps (supports filters)
    elif arg == "list":
        pass
        # (mod = value)
        # filtering by rating / players / author / date
    else:
        pass
        # download map by hash (hash = arg)

# Crash Reports API

def upload_logs_and_replay():
    pass


# Map Triggers

def recalculate_hashes():
    # this function recalculates hashes for all existing maps and updates DB
    pass

def map_upgrade():
    # this function upgrades all existings maps using OpenRA.Utility and triggers recalculate_hashes() function
    pass
