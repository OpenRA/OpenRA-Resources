import os
import json
import base64
from django.http import Http404
from django.http import HttpResponse
from openraData.models import Maps
from django.contrib.auth.models import User
# Map API

def mapAPI(request, arg, value="", apifilter="", filtervalue=""):
    # get detailed map info by title
    if arg == "title":
        title = value.lower()
        try:
            mapObject = Maps.objects.get(title__icontains=title)
        except:
            raise Http404
        response_data = serialize_basic_map_info(mapObject)
        return HttpResponse(json.dumps(response_data), content_type="application/json")
    
    # get detailed map info by hash
    elif arg == "hash":
        map_hash = value
        try:
            mapObject = Maps.objects.get(map_hash=map_hash)
        except:
            raise Http404
        response_data = serialize_basic_map_info(mapObject)
        return HttpResponse(json.dumps(response_data), content_type="application/json")
    
    # get URL of map by hash
    elif arg == "url":
        map_hash = value
        try:
            mapObject = Maps.objects.get(map_hash=map_hash)
        except:
            raise Http404
        url = "http://" + request.META['HTTP_HOST'] + "/maps/" + str(mapObject.id).rjust(7, '0') + "/oramap"
        last_revision = True
        if mapObject.next_rev != 0:
            last_revision = False
        response_data = {}
        response_data['id'] = mapObject.id
        response_data['url'] = url
        response_data['map_hash'] = mapObject.map_hash
        response_data['revision'] = mapObject.revision
        response_data['last_revision'] = last_revision
        return HttpResponse(json.dumps(response_data), content_type="application/json")
    
    # get minimap preview by hash (represented in JSON by encoded into base64)
    elif arg == "minimap":
        map_hash = value
        try:
            mapObject = Maps.objects.get(map_hash=map_hash)
        except:
            raise Http404
        
        minimap = get_minimap(mapObject.id)
        url = get_url(request, mapObject.id)

        last_revision = True
        if mapObject.next_rev != 0:
            last_revision = False
        response_data = {}
        response_data['id'] = mapObject.id
        response_data['minimap'] = minimap
        response_data['url'] = url
        response_data['map_hash'] = mapObject.map_hash
        response_data['revision'] = mapObject.revision
        response_data['last_revision'] = last_revision
        return HttpResponse(json.dumps(response_data), content_type="application/json")
    
    # get detailed map info + encoded minimap + URL for a range of maps (supports filters)
    elif arg == "list":
        mod = value
        if mod == "":
            raise Http404
        if apifilter != "":
            if apifilter not in ["rating", "-rating", "players", "-players", "posted", "-posted", "author", "uploader"]:
                raise Http404
        try:
            mapObject = Maps.objects.all().filter(game_mod=mod.lower())
            if apifilter == "players":
                mapObject = mapObject.order_by("-players")
            if apifilter == "-players":
                mapObject = mapObject.order_by("players")
            if apifilter == "posted":
                mapObject = mapObject.order_by("-posted")
            if apifilter == "-posted":
                mapObject = mapObject.order_by("posted")
            if apifilter == "rating":
                mapObject = mapObject.order_by("-rating_score")
            if apifilter == "-rating":
                mapObject = mapObject.order_by("rating_score")
            if apifilter == "author":
                if filtervalue != "":
                    mapObject = mapObject.filter(author__iexact=filtervalue.lower())
            if apifilter == "uploader":
                if filtervalue != "":
                    try:
                        u = User.objects.get(username__iexact=filtervalue.lower())
                        mapObject = mapObject.filter(user_id=u.id)
                    except:
                        pass
        except:
            raise Http404
        basic_response = []
        for item in mapObject:
            minimap = get_minimap(item.id, True)
            url = get_url(request, item.id)
            response_data = serialize_basic_map_info(item)
            response_data['minimap'] = minimap
            response_data['url'] = url
            basic_response.append(response_data)

        return HttpResponse(json.dumps(basic_response), content_type="application/json")
    else:
        # serve application/zip by hash
        oramap = ""
        try:
            mapObject = Maps.objects.get(map_hash=arg)
        except:
            raise Http404
        if not mapObject.downloading:
            raise Http404
        path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/maps/' + str(mapObject.id).rjust(7, '0')
        try:
            mapDir = os.listdir(path)
        except:
            raise Http404
        for filename in mapDir:
            if filename.endswith(".oramap"):
                oramap = filename
                break
        if oramap == "":
            raise Http404
        serveOramap = path + os.sep + oramap
        oramap = os.path.splitext(oramap)[0] + "-" + str(mapObject.revision) + ".oramap"
        response = HttpResponse(open(serveOramap), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename = "%s"' % oramap
        return response

def serialize_basic_map_info(mapObject):
    last_revision = True
    if mapObject.next_rev != 0:
        last_revision = False
    response_data = {}
    response_data['id'] = mapObject.id
    response_data['title'] = mapObject.title
    response_data['description'] = mapObject.description
    response_data['info'] = mapObject.info
    response_data['author'] = mapObject.author
    response_data['map_type'] = mapObject.map_type
    response_data['players'] = mapObject.players
    response_data['game_mod'] = mapObject.game_mod
    response_data['map_hash'] = mapObject.map_hash
    response_data['width'] = mapObject.width
    response_data['height'] = mapObject.height
    response_data['tileset'] = mapObject.tileset
    response_data['revision'] = mapObject.revision
    response_data['last_revision'] = last_revision
    response_data['requires_upgrade'] = mapObject.requires_upgrade
    response_data['advanced_map'] = mapObject.advanced_map
    response_data['lua'] = mapObject.lua
    response_data['posted'] = str(mapObject.posted)
    response_data['viewed'] = mapObject.viewed
    response_data['rating_votes'] = mapObject.rating_votes
    response_data['rating_score'] = mapObject.rating_score
    return response_data

def get_minimap(mapid, soft=False):
    minimap = ""
    path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/maps/' + str(mapid).rjust(7, '0')
    try:
        mapDir = os.listdir(path)
    except:
        if soft:
            return ""
        else:
            raise Http404
    for filename in mapDir:
        if filename.endswith("-mini.png"):
            minimap = filename
            break
    if minimap == "":
        if soft:
            return ""
        else:
            raise Http404
    with open(path + os.sep + minimap, "rb") as image_file:
        minimap = base64.b64encode(image_file.read())
    return minimap

def get_url(request, mapid):
    url = "http://" + request.META['HTTP_HOST'] + "/maps/" + str(mapid).rjust(7, '0') + "/oramap"
    return url