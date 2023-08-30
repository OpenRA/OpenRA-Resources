import base64
import json
import os

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, get_list_or_404

from openra.models import Maps
from openra.models import MapCategories
from openra import misc

# pylint: disable=too-many-locals


def __generate_response(maps_data, yaml):
    if yaml:
        yaml_response = ""
        for map_hash, map_data in maps_data.items():
            yaml_response += map_hash + ':\n'
            for map_key, map_value in map_data.items():
                value = str(map_value)
                if isinstance(map_value, list):
                    value = ', '.join(map_value)

                # Escape bad yaml values
                value = value.replace('\r', '\\r').replace('\n', '\\n').replace('\t', '\\t')
                yaml_response += '\t{0}: {1}\n'.format(map_key, value)
        response = StreamingHttpResponse(yaml_response, content_type="text/plain")
    else:
        response = JsonResponse(list(maps_data.values()),
                                safe=False,
                                json_dumps_params={'indent': 4})

    response['Access-Control-Allow-Origin'] = '*'
    return response


def __map_info_from_objects(request, map_objects, yaml):
    results = {}
    for map_object in map_objects:
        last_revision = True
        if map_object.next_rev != 0:
            last_revision = False

        license_label, _ = misc.selectLicenceInfo(map_object)
        if license_label is not None:
            license_label = "Creative Commons " + license_label
        else:
            license_label = "null"

        # TODO: Read this from the mod id / parser model once this has been added
        map_grid_type = 'Rectangular'  # ra/cnc/d2k
        if map_object.game_mod in ['ts', 'ra2', 'sp']:
            map_grid_type = 'RectangularIsometric'

        # TODO: Reimplement categories in a nicer way
        category_list = []
        if map_object.categories:
            categories = json.loads(map_object.categories)
            category_ids = [cat_id.strip('_') for cat_id in categories]
            category_objects = MapCategories.objects.filter(id__in=category_ids)
            category_list = [c.category_name for c in category_objects]

        minimap_path = os.path.join(
            settings.BASE_DIR, 'openra', 'data', 'maps',
            str(map_object.id), 'content', 'map.png')

        if os.path.exists(minimap_path):
            with open(minimap_path, 'rb') as image_file:
                minimap = base64.b64encode(image_file.read()).decode()
        else:
            minimap = ''

        download_url = 'http://' + request.META.get('HTTP_HOST', 'resource.openra.net') + \
                       '/maps/' + str(map_object.id) + '/oramap'

        # TODO: Title and author have ' replaced with '' before insertion into the database. Work out why and fix it
        results[map_object.map_hash] = {
            'id': map_object.id,
            'uploader': map_object.user.username,
            'title': map_object.title.replace("''", "'"),
            'description': map_object.description,
            'info': map_object.info,
            'author': map_object.author.replace("''", "'"),
            'map_type': map_object.map_type,
            'players': map_object.players,
            'game_mod': map_object.game_mod,
            'map_hash': map_object.map_hash,
            'width': map_object.width,
            'height': map_object.height,
            'bounds': map_object.bounds,
            'spawnpoints': map_object.spawnpoints,
            'tileset': map_object.tileset,
            'revision': map_object.revision,
            'last_revision': last_revision,
            'requires_upgrade': map_object.requires_upgrade,
            'advanced_map': map_object.advanced_map,
            'lua': map_object.lua,
            'posted': str(map_object.posted),
            'viewed': map_object.viewed,
            'downloaded': map_object.downloaded,
            'rating': map_object.rating,
            'license': license_label,
            'minimap': minimap,
            'url': download_url,
            'downloading': map_object.downloading,
            'mapformat': map_object.mapformat,
            'parser': map_object.parser,
            'map_grid_type': map_grid_type,
            'categories': category_list,
            'rules': map_object.base64_rules,
            'players_block': map_object.base64_players,
            'reports': map_object.amount_reports,
        }

    return __generate_response(results, yaml)


def map_info_from_hashes(request, map_hashes, yaml=False):
    """Map info queried from a comma delimited list of SHA1 hashes"""
    map_objects = get_list_or_404(Maps, map_hash__in=map_hashes.split(','))
    return __map_info_from_objects(request, map_objects, yaml)


def map_info_from_ids(request, map_ids, yaml=False):
    """Map info queried from a comma delimited list of resource center map IDs"""
    map_objects = get_list_or_404(Maps, id__in=map_ids.split(','))
    return __map_info_from_objects(request, map_objects, yaml)


def map_urlinfo_from_hashes(request, map_hashes, yaml=False):
    """Map url and revision info queried from a comma delimited list of SHA1 hashes"""
    map_objects = Maps.objects.filter(map_hash__in=map_hashes.split(','))
    if not map_objects:
        raise Http404

    results = {}
    for map_object in map_objects:
        download_url = 'http://' + request.META['HTTP_HOST'] + \
                       '/maps/' + str(map_object.id) + '/oramap'
        results[map_object.map_hash] = {
            'id': map_object.id,
            'url': download_url,
            'revision': map_object.revision,
            'last_revision': map_object.next_rev == 0,
            'map_hash': map_object.map_hash
        }

    return __generate_response(results, yaml)


def latest_map_info(request, yaml=False):
    """Map info queried from the latest uploaded map"""
    try:
        map_objects = [Maps.objects.latest('id')]
    except ObjectDoesNotExist:
        raise Http404

    return __map_info_from_objects(request, map_objects, yaml)


def download_map(request, map_hash):
    """Map archive queried from a single SHA1 hash"""
    map_object = get_object_or_404(Maps, map_hash=map_hash, downloading=True)
    if not map_object.downloading or map_object.amount_reports >= settings.REPORTS_PENALTY_AMOUNT:
        raise Http404

    source_path = os.path.join(settings.BASE_DIR, 'openra', 'data', 'maps', str(map_object.id))
    oramap_name = misc.first_oramap_in_directory(source_path)
    if not oramap_name:
        raise Http404

    serve_filename = os.path.splitext(oramap_name)[0] + '-' + str(map_object.revision) + '.oramap'
    oramap_path = os.path.join(source_path, oramap_name)
    response = StreamingHttpResponse(open(oramap_path, 'rb'), content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename = %s' % serve_filename
    response['Content-Length'] = os.path.getsize(oramap_path)

    Maps.objects.filter(id=map_object.id).update(downloaded=map_object.downloaded + 1)
    return response
