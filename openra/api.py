import os
import json
import base64
import cgi
from django.conf import settings
from django.http import Http404
from django.http import StreamingHttpResponse

from openra.models import Maps
from openra.models import MapCategories
from openra import misc


# Map API
def mapAPI(request, arg, arg1="", arg2=""):
    # get detailed map info by hash
    if arg == "hash":
        map_hashes = arg1.split(',')
        mapObject = Maps.objects.filter(map_hash__in=map_hashes).distinct('map_hash')
        if not mapObject:
            raise Http404
        if arg2 == "yaml":
            yaml_response = ""
            for item in mapObject:
                yaml_response += serialize_basic_map_info(request, item, "yaml")
            if yaml_response == "":
                raise Http404
            response = StreamingHttpResponse(yaml_response, content_type="text/plain")
            response['Access-Control-Allow-Origin'] = '*'
            return response
        else:
            json_response = []
            for item in mapObject:
                json_response.append(serialize_basic_map_info(request, item))
            if len(json_response) == 0:
                raise Http404
            response = StreamingHttpResponse(json.dumps(json_response, indent=4), content_type="application/javascript")
            response['Access-Control-Allow-Origin'] = '*'
            return response

    # get detailed map info by ID
    elif arg == "id":
        map_IDs = arg1.split(',')
        mapObject = Maps.objects.filter(id__in=map_IDs)
        if not mapObject:
            raise Http404
        if arg2 == "yaml":
            yaml_response = ""
            for item in mapObject:
                yaml_response += serialize_basic_map_info(request, item, "yaml")
            if yaml_response == "":
                raise Http404
            response = StreamingHttpResponse(yaml_response, content_type="text/plain")
            response['Access-Control-Allow-Origin'] = '*'
            return response
        else:
            json_response = []
            for item in mapObject:
                json_response.append(serialize_basic_map_info(request, item))
            if len(json_response) == 0:
                raise Http404
            response = StreamingHttpResponse(json.dumps(json_response, indent=4), content_type="application/javascript")
            response['Access-Control-Allow-Origin'] = '*'
            return response

    # get URL of map by hash
    elif arg == "url":
        map_hashes = arg1.split(',')
        mapObject = Maps.objects.filter(map_hash__in=map_hashes)
        if not mapObject:
            raise Http404
        if arg2 == "yaml":
            yaml_response = ""
            for item in mapObject:
                yaml_response += serialize_url_map_info(request, item, "yaml")
            if yaml_response == "":
                raise Http404
            response = StreamingHttpResponse(yaml_response, content_type="text/plain")
            response['Access-Control-Allow-Origin'] = '*'
            return response
        else:
            json_response = []
            for item in mapObject:
                json_response.append(serialize_url_map_info(request, item))
            if len(json_response) == 0:
                raise Http404
            response = StreamingHttpResponse(json.dumps(json_response, indent=4), content_type="application/javascript")
            response['Access-Control-Allow-Origin'] = '*'
            return response
    elif arg == "lastmap":
        mapObject = Maps.objects.latest('id')
        if arg1 == "yaml":
            yaml_response = serialize_basic_map_info(request, mapObject, "yaml")
            if yaml_response == "":
                raise Http404
            response = StreamingHttpResponse(yaml_response, content_type="text/plain")
            response['Access-Control-Allow-Origin'] = '*'
            return response
        else:
            json_response = []
            json_response.append(serialize_basic_map_info(request, mapObject))
            if len(json_response) == 0:
                raise Http404
            response = StreamingHttpResponse(json.dumps(json_response, indent=4), content_type="application/javascript")
            response['Access-Control-Allow-Origin'] = '*'
            return response
    else:
        # serve application/zip by hash
        oramap = ""
        try:
            mapObject = Maps.objects.filter(map_hash=arg,downloading=True)[0]
        except:
            raise Http404
        if not mapObject.downloading:
            raise Http404
        if mapObject.amount_reports >= settings.REPORTS_PENALTY_AMOUNT:
            raise Http404
        path = os.path.join(settings.BASE_DIR, __name__.split('.')[0], 'data', 'maps', str(mapObject.id))
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
        serveOramap = os.path.join(path, oramap)
        oramap = os.path.splitext(oramap)[0] + "-" + str(mapObject.revision) + ".oramap"
        response = StreamingHttpResponse(open(serveOramap, 'rb'), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename = %s' % oramap
        response['Content-Length'] = os.path.getsize(serveOramap)
        Maps.objects.filter(id=mapObject.id).update(downloaded=mapObject.downloaded+1)
        return response


def serialize_url_map_info(request, mapObject, yaml=""):
    url = get_url(request, mapObject.id)
    last_revision = True
    if mapObject.next_rev != 0:
        last_revision = False
    if yaml:
        response_data = """
{0}:
\tid: {1}
\turl: {2}
\trevision: {3}
\tlast_revision: {4}\n""".format(
            mapObject.map_hash,
            mapObject.id,
            url,
            mapObject.revision,
            last_revision,
        ).lstrip()
        return response_data
    response_data = {}
    response_data['id'] = mapObject.id
    response_data['url'] = url
    response_data['map_hash'] = mapObject.map_hash
    response_data['revision'] = mapObject.revision
    response_data['last_revision'] = last_revision
    return response_data


def serialize_basic_map_info(request, mapObject, yaml=""):
    minimap = get_minimap(mapObject.id, True)
    url = get_url(request, mapObject.id)
    last_revision = True
    if mapObject.next_rev != 0:
        last_revision = False
    license, icons = misc.selectLicenceInfo(mapObject)
    if license is not None:
        license = "Creative Commons " + license
    else:
        license = "null"

    map_grid_type = 'Rectangular'  # ra/cnc/d2k
    if mapObject.game_mod in ['ts', 'ra2', 'sp']:
        map_grid_type = 'RectangularIsometric'

    category_lst = []
    if mapObject.categories:
        categories = json.loads(mapObject.categories)
        for cat_id in categories:
            catObj = MapCategories.objects.filter(id=cat_id.strip('_')).first()
            if catObj:
                category_lst.append(catObj.category_name)

    if yaml:
        response_data = u"""
{0}:
\tid: {1}
\ttitle: {2}
\tdescription: {3}
\tauthor: {4}
\tmap_type: {5}
\tplayers: {6}
\tgame_mod: {7}
\twidth: {8}
\theight: {9}
\tbounds: {10}
\tspawnpoints: {11}
\ttileset: {12}
\trevision: {13}
\tlast_revision: {14}
\trequires_upgrade: {15}
\tadvanced_map: {16}
\tlua: {17}
\tposted: {18}
\tviewed: {19}
\tdownloaded: {20}
\trating: {21}
\tlicense: {22}
\tminimap: {23}
\turl: {24}
\tdownloading: {25}
\tmapformat: {26}
\tparser: {27}
\tmap_grid_type: {28}
\tcategories: {29}
\trules: {30}
\tplayers_block: {31}
\treports: {32}\n""".format(
            mapObject.map_hash,
            mapObject.id,
            cgi.escape(mapObject.title, quote=None),
            cgi.escape(mapObject.description, quote=None),
            cgi.escape(mapObject.author.encode('utf-8').decode('utf-8'), quote=None),
            cgi.escape(mapObject.map_type, quote=None),
            mapObject.players,
            cgi.escape(mapObject.game_mod, quote=None),
            mapObject.width,
            mapObject.height,
            mapObject.bounds,
            mapObject.spawnpoints,
            cgi.escape(mapObject.tileset, quote=None),
            mapObject.revision,
            last_revision,
            mapObject.requires_upgrade,
            mapObject.advanced_map,
            mapObject.lua,
            str(mapObject.posted),
            mapObject.viewed,
            mapObject.downloaded,
            mapObject.rating,
            license,
            minimap,
            url,
            mapObject.downloading,
            mapObject.mapformat,
            mapObject.parser,
            map_grid_type,
            cgi.escape(", ".join(category_lst), quote=None),
            mapObject.base64_rules,
            mapObject.base64_players,
            mapObject.amount_reports
        ).replace("''", "'").lstrip()
        return response_data
    response_data = {}
    response_data['id'] = mapObject.id
    response_data['title'] = cgi.escape(mapObject.title, quote=None).replace("''", "'")
    response_data['description'] = cgi.escape(mapObject.description, quote=None).replace("''", "'")
    response_data['info'] = cgi.escape(mapObject.info, quote=None).replace("''", "'")
    response_data['author'] = cgi.escape(mapObject.author, quote=None).replace("''", "'")
    response_data['map_type'] = cgi.escape(mapObject.map_type, quote=None).replace("''", "'")
    response_data['players'] = mapObject.players
    response_data['game_mod'] = cgi.escape(mapObject.game_mod, quote=None).replace("''", "'")
    response_data['map_hash'] = mapObject.map_hash
    response_data['width'] = mapObject.width
    response_data['height'] = mapObject.height
    response_data['bounds'] = mapObject.bounds
    response_data['spawnpoints'] = mapObject.spawnpoints
    response_data['tileset'] = cgi.escape(mapObject.tileset, quote=None)
    response_data['revision'] = mapObject.revision
    response_data['last_revision'] = last_revision
    response_data['requires_upgrade'] = mapObject.requires_upgrade
    response_data['advanced_map'] = mapObject.advanced_map
    response_data['lua'] = mapObject.lua
    response_data['posted'] = str(mapObject.posted)
    response_data['viewed'] = mapObject.viewed
    response_data['downloaded'] = mapObject.downloaded
    response_data['rating'] = mapObject.rating
    response_data['license'] = license
    response_data['minimap'] = minimap
    response_data['url'] = url
    response_data['downloading'] = mapObject.downloading
    response_data['mapformat'] = mapObject.mapformat
    response_data['parser'] = mapObject.parser
    response_data['map_grid_type'] = map_grid_type
    response_data['categories'] = category_lst
    response_data['rules'] = mapObject.base64_rules
    response_data['players_block'] = mapObject.base64_players
    response_data['reports'] = mapObject.amount_reports
    return response_data


def get_minimap(mapid, soft=False):
    minimap = ""
    path = os.path.join(settings.BASE_DIR, __name__.split('.')[0], 'data', 'maps', str(mapid))

    try:
        contentDir = os.listdir(os.path.join(path, 'content'))
    except:
        if soft:
            return ""
        else:
            raise Http404
    for filename in contentDir:
        if filename == "map.png":
            minimap = filename
            serveImage = os.path.join(path, 'content', minimap)
            break

    if minimap == "":
        mapDir = os.listdir(path)
        for filename in mapDir:
            if filename.endswith("-mini.png"):
                minimap = filename
                serveImage = os.path.join(path, minimap)
                break
    if minimap == "":
        if soft:
            return ""
        else:
            raise Http404
    with open(serveImage, "rb") as image_file:
        minimap = base64.b64encode(image_file.read()).decode()
    return minimap


def get_url(request, mapid):
    url = "http://" + request.META['HTTP_HOST'] + "/maps/" + str(mapid) + "/oramap"
    return url
