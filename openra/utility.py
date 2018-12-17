import base64
import json
import os
import zipfile

from subprocess import Popen, PIPE
from django.conf import settings
from django.utils import timezone
from openra.models import MapCategories


def detect_mimetype(path):
    """Runs the file command and returns a tuple of returncode, mimetype"""
    popen = Popen(['file', '-b', '--mime-type', path], stdout=PIPE)
    output = b''
    for chunk in popen.stdout:
        output += chunk

    popen.wait()
    return popen.returncode, output.decode().strip()


def run_utility_command(parser, game_mod, args, cwd=None):
    """Runs an OpenRA.Utility command and returns a tuple of returncode, output text"""
    # HACK: Work around unknown third-party mods
    # This can go away once mods are defined as a Django model
    game_mod = game_mod.lower()
    if game_mod not in ['ra', 'cnc', 'd2k', 'ts']:
        game_mod = 'ra'

    popen = Popen(['mono', '--debug',
                   os.path.join(settings.OPENRA_ROOT_PATH, parser, 'OpenRA.Utility.exe'),
                   game_mod] + args, stdout=PIPE, cwd=cwd)

    output = b''
    for chunk in popen.stdout:
        output += chunk

    popen.wait()
    return popen.returncode, output.decode().strip()


def parse_map_metadata(oramap_path):
    # TODO: Replace this DIY parsing with a utility command that returns JSON
    # TODO: Will need a migration to remove the quote-doubling from title and author
    metadata = {
        'mapformat': 0,
        'lua': False,
        'players': 0,
        'title': '',
        'author': '',
        'tileset': '',
        'categories': '',
        'width': 0,
        'height': 0,
        'bounds': '0,0,0,0',
        'base64_players': ''
    }

    yaml_data = ""
    with zipfile.ZipFile(oramap_path, mode='a') as oramap:
        for name in oramap.namelist():
            if name == "map.yaml":
                yaml_data = oramap.read(name).decode("utf-8")
            if name.endswith('.lua'):
                metadata['lua'] = True

    if not yaml_data:
        return None

    in_players_node = False
    in_actors_node = False
    in_spawn_node = False

    spawn_locations = []
    players_nodes = ''

    for line in yaml_data.split('\n'):
        # Count starting indent
        space_indent = 0
        tab_indent = 0
        for char in line:
            if char not in [' ', '\t']:
                break
            if char == '\t':
                tab_indent += 1
            else:
                space_indent += 1
        indent = int(tab_indent + space_indent // 4)

        if in_players_node and indent == 0:
            in_players_node = False
        if in_actors_node and indent == 0:
            in_actors_node = False
        if in_spawn_node and indent < 2:
            in_spawn_node = False

        if in_players_node:
            players_nodes += '\t' * indent + line.strip() + '\n'

        split_index = line.find(':')
        if split_index < 0:
            continue

        key = line[:split_index].strip()
        value = line[split_index + 1:].strip()
        if key == 'Title':
            metadata['title'] = value.replace("'", "''")
        elif key == 'RequiresMod':
            metadata['game_mod'] = value.lower()
        elif key == 'Author':
            metadata['author'] = value.replace("'", "''")
        elif key == 'Tileset':
            metadata['tileset'] = value
        elif key == 'Categories':
            # TODO: Migrate this to something sensible!
            category_ids = []
            for category_item in value.split(','):
                category = MapCategories.objects.filter(category_name=category_item.strip()).first()
                if not category:
                    category_transac = MapCategories(
                        category_name=category_item.strip(),
                        posted=timezone.now(),
                    )
                    category_transac.save()
                    category_ids.append('_'+str(category_transac.id)+'_')
                else:
                    category_ids.append('_'+str(category.id)+'_')
            metadata['categories'] = json.dumps(category_ids)
        elif key == 'MapSize':
            size = value.split(',')
            metadata['width'] = size[0]
            metadata['height'] = size[1]
        elif key == 'Bounds':
            metadata['bounds'] = value
        elif key == 'MapFormat':
            metadata['mapformat'] = int(value)
        elif key == 'Actors':
            in_actors_node = True
        elif in_actors_node and value.lower() == 'mpspawn':
            in_spawn_node = True
        elif in_spawn_node and key == "Location":
            spawn_locations.append(value)

        elif key == 'Players':
            in_players_node = True
        elif in_players_node and key == 'Playable':
            if value.lower() in ['true', 'on', 'yes', 'y']:
                metadata['players'] += 1

    metadata['spawnpoints'] = ', '.join(spawn_locations)

    if players_nodes:
        metadata['base64_players'] = base64.b64encode(players_nodes.encode()).decode()

    return metadata
