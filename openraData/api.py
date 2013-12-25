from django.http import HttpResponse

# Map API

def mapAPI(request, arg, value="", filter=""):
    # get detailed map info by title
    if arg == "title":
        return HttpResponse()
        # map info by title (title = value)
    
    # get detailed map info by hash
    elif arg == "hash":
        return HttpResponse()
        # map info by hash (hash = value)
    
    # get URL of map by hash
    elif arg == "url":
        return HttpResponse()
        # map url by hash (hash = value)
    
    # get minimap preview by hash (represented in JSON by encoded into base64)
    elif arg == "minimap":
        return HttpResponse()
        # minimap.png for map in JSON format encoded into base64 (hash = value)
    
    # get detailed map info + encoded minimap + URL for a range of maps (supports filters)
    elif arg == "list":
        return HttpResponse()
        # (mod = value)
        # filtering by rating / players / author / date
    else:
        return HttpResponse()
        # download map by hash (hash = arg)
