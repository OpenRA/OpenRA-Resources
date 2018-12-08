import base64
import json
import os
import shutil
import tempfile
import zipfile

from subprocess import Popen, PIPE
from django.conf import settings
from django.utils import timezone
from openra.models import Maps, Lints, MapCategories, MapUpgradeLogs
from openra import misc

def __first_oramap_in_directory(path):
    """Returns the first matching .oramap filename in a given path or None

       The returned string is not prefixed by the directory.

       TODO: This helper is a workaround for the filename not being stored in the model
       This really should be fixed, and then this helper removed!
    """
    for filename in os.listdir(path):
        if filename.endswith('.oramap'):
            return filename
    return None

def __run_utility_command(parser, game_mod, args):
    """Runs an OpenRA.Utility command and returns a tuple of returncode, output text"""
    # HACK: Work around unknown third-party mods
    # This can go away once mods are defined as a Django model
    game_mod = game_mod.lower()
    if game_mod not in ['ra', 'cnc', 'd2k', 'ts']:
        game_mod = 'ra'

    popen = Popen(['mono', '--debug',
                   os.path.join(settings.OPENRA_ROOT_PATH, parser, 'OpenRA.Utility.exe'),
                   game_mod] + args, stdout=PIPE)

    output = b''
    for chunk in popen.stdout:
        output += chunk

    popen.wait()
    return popen.returncode, output.decode()

def parse_map_metadata(oramap_path):

    # TODO: Replace this DIY parsing with a utility command that returns JSON
    metadata = {
        'lua': False,
        'players': 0,
        'title': '',
        'author': '',
        'description': '',
        'map_type': '',
        'categories': '',
        'shellmap': False,
        'base64_players': ''
    }

    yaml_data = ""
    with zipfile.ZipFile(oramap_path, mode='a') as z:
        for name in z.namelist():
            if name == "map.yaml":
                yaml_data = z.read(name).decode("utf-8")
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
        for c in line:
            if c not in [' ', '\t']:
                break
            if c == '\t':
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
            for c in value.split(','):
                category = MapCategories.objects.filter(category_name=c.strip()).first()
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
        elif key == 'Visibility' and 'Shellmap' in value.split(','):
            metadata['shellmap'] = True

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


def map_update(item, parser=settings.OPENRA_VERSIONS[0]):
    """Create a new revision of a map by running the OpenRA.Utility
       update command using a given parser version

       Returns the updated map revision or None on failure
    """
    print('Starting map update action on map {}. Using parser: {}'.format(item.id, parser))
    if item.next_rev != 0:
        print('Update failed: a newer revision of this map already exists')
        return None

    # Find the oramap file in the data directory
    source_path = os.path.join(settings.BASE_DIR, 'openra', 'data', 'maps', str(item.id))
    oramap_filename = __first_oramap_in_directory(source_path)
    if not oramap_filename:
        print('Update failed: map directory does not contain an .oramap package')
        return None

    # Create a temporary working directory and copy the oramap to it
    # Directory is automatically deleted when exiting the context manager
    with tempfile.TemporaryDirectory() as working_path:
        print('Temporary working directory: {}'.format(working_path))
        oramap_path = os.path.join(working_path, oramap_filename)
        shutil.copy(os.path.join(source_path, oramap_filename), oramap_path)

        # Run OpenRA.Utility to do the actual update
        print('Running --update-map')
        update_retcode, update_output = __run_utility_command(parser, item.game_mod, [
            '--update-map',
            oramap_path,
            item.parser,
            '--apply'
        ])

        # Error code if the command crashed, usage line on invalid arguments
        if update_retcode != 0 or update_output.startswith('--update-map MAP SOURCE'):
            print('Update failed: OpenRA.Utility --update-map returned an error')
            return None

        if not update_output:
            print('Update failed: OpenRA.Utility --update-map returned no output')
            return None

        if update_output.startswith('No such command'):
            print('Update failed: OpenRA.Utility --update-map command missing')
            return None

        # Recalculate the map UID/hash
        # TODO: extract this into a rewritten map_hash function so it can be reused by the upload handler
        print('Running --map-hash')
        hash_retcode, new_map_uid = __run_utility_command(parser, item.game_mod, [
            '--map-hash', oramap_path])

        if hash_retcode != 0 or not new_map_uid:
            print('Update failed: Hash calculation failed')
            return None

        # Extract the oramap contents (Why?!?)
        unzipped_map = UnzipMap(item, oramap_path)
        if not unzipped_map:
            print('Update failed: Content extraction failed')
            return None

        # Parse map metadata
        metadata = parse_map_metadata(oramap_path)
        if not metadata:
            print('Update failed: Metadata parsing failed')
            return None

        # Parse custom rules
        rules_retcode, custom_rules = __run_utility_command(parser, item.game_mod, [
            '--map-rules', oramap_path])

        if rules_retcode != 0:
            print('Update failed: Rule extraction failed')
            return None

        # TODO: Check against the game's Ruleset.DefinesUnsafeCustomRules code instead of line count
        advanced = len(custom_rules.split("\n")) > 8
        base64_rules = base64.b64encode(custom_rules.encode()).decode()

        updated_item = Maps(
            user=item.user,
            title=metadata['title'],
            description=metadata['description'],
            info=item.info,
            author=metadata['author'],
            map_type=metadata['map_type'],
            categories=metadata['categories'],
            players=metadata['players'],
            game_mod=metadata['game_mod'],
            map_hash=new_map_uid,
            width=metadata['width'],
            height=metadata['height'],
            bounds=metadata['bounds'],
            mapformat=metadata['mapformat'],
            spawnpoints=metadata['spawnpoints'],
            tileset=metadata['tileset'],
            shellmap=metadata['shellmap'],
            base64_rules=base64_rules,
            base64_players=metadata['base64_players'],
            legacy_map=False,
            revision=item.revision + 1,
            pre_rev=item.id,
            next_rev=0,
            downloading=True,
            requires_upgrade=True,
            advanced_map=advanced,
            lua=metadata['lua'],
            posted=item.posted, # keep the original date to avoid reordering the map list
            viewed=0,
            policy_cc=item.policy_cc,
            policy_commercial=item.policy_commercial,
            policy_adaptations=item.policy_adaptations,
            parser=parser,
        )

        updated_item.save()

        # Copy the updated map to its new data location
        new_path = os.path.join(settings.BASE_DIR, 'openra', 'data', 'maps', str(updated_item.id))
        if not os.path.exists(new_path):
            os.makedirs(os.path.join(new_path, 'content'))

        # Point the original map's next revision to the new map
        Maps.objects.filter(id=item.id).update(next_rev=updated_item.id)

        # Update logs are only interesting if the map has custom rules
        if item.advanced_map:
            log = MapUpgradeLogs(
                map_id=updated_item,
                from_version=item.parser,
                to_version=parser,
                date_run=timezone.now(),
                upgrade_output=update_output
            )
            log.save()

        # Copy old content to the new revision dir (Why!?!)
        misc.copytree(source_path, new_path)

        # Copy updated content from temp dir to the new revision dir
        misc.copytree(working_path, new_path)

        print('Update complete. New ID is {}'.format(updated_item.id))

        # Test the updated map
        # TODO: extract this into a rewritten map_lint function so it can be reused by the upload handler
        print('Running --check-yaml')
        lint_retcode, lint_output = __run_utility_command(parser, item.game_mod, [
            '--check-yaml',
            oramap_path,
        ])

        if lint_output:
            lint = Lints(
                item_type='maps',
                map_id=updated_item.id,
                version_tag=parser,
                pass_status=lint_retcode == 0,
                lint_output=lint_output,
                posted=timezone.now(),
            )
            lint.save()

        return updated_item

def recalculate_hash(item, fullpath="", parser=settings.OPENRA_VERSIONS[0]):

    if fullpath == "":
        path = os.path.join(settings.BASE_DIR, 'openra', 'data', 'maps', str(item.id))
        filename = ""
        Dir = os.listdir(path)
        for fn in Dir:
            if fn.endswith('.oramap'):
                filename = fn
                break
        if filename == "":
            print('Failed to recalculate hash for %s: %s' % (item.id, 'can not find map'))
            return {'response': 'can not find map', 'error': True, 'maphash': 'none'}
        fullpath = os.path.join(path, filename)

    os.chmod(fullpath, 0o444)

    command = misc.build_utility_command(parser, item.game_mod, ['--map-hash', fullpath])
    proc = Popen(command.split(), stdout=PIPE).communicate()

    os.chmod(fullpath, 0o644)

    maphash = proc[0].decode().strip()
    print('Recalculated hash: %s' % item.id)

    return {'response': 'success', 'error': False, 'maphash': maphash}


def ReadYaml(item=False, fullpath=""):
    if fullpath == "":
        if item is False:
            return {'response': 'wrong method call', 'error': True}
        path = os.path.join(settings.BASE_DIR, 'openra', 'data', 'maps', str(item.id))
        Dir = os.listdir(path)
        for fn in Dir:
            if fn.endswith('.oramap'):
                fullpath = os.path.join(path, fn)
                break
        if fullpath == "":
            return {'response': 'could not find .oramap', 'error': True}
    map_data_ordered = {}
    map_data_ordered['lua'] = False
    map_data_ordered['advanced'] = False
    map_data_ordered['players'] = 0
    map_data_ordered['author'] = ""
    map_data_ordered['description'] = ""
    map_data_ordered['map_type'] = ""
    map_data_ordered['categories'] = ""
    map_data_ordered['shellmap'] = False

    z = zipfile.ZipFile(fullpath, mode='a')
    yamlData = ""
    for zfn in z.namelist():
        if zfn == "map.yaml":
            mapbytes = z.read(zfn)
            yamlData = mapbytes.decode("utf-8")
        if zfn.endswith('.lua'):
            map_data_ordered['lua'] = True
    z.close()
    if yamlData == "":
        return {'response': 'Failed. Invalid map format.', 'error': True}

    countAdvanced = 0
    shouldCountRules = False

    inPlayersBlock = False
    map_data_ordered['base64_players'] = ''

    expectspawn = False
    spawnpoints = ""
    for line in yamlData.split('\n'):

        if line[0:5] == "Title":
            map_data_ordered['title'] = line[6:].strip().replace("'", "''")

        if line[0:11] == "RequiresMod":
            map_data_ordered['game_mod'] = line[12:].strip().lower()

        if line[0:6] == "Author":
            map_data_ordered['author'] = line[7:].strip().replace("'", "''")

        if line[0:7] == "Tileset":
            map_data_ordered['tileset'] = line[8:].strip()

        if line[0:4] == "Type":  # gone in MapFormat 11
            map_data_ordered['map_type'] = line[5:].strip()

        if "Categories:" in line:
            category_id_list = []
            for category_item in line.split(':')[1].strip().split(','):
                category = MapCategories.objects.filter(category_name=category_item.strip()).first()
                if not category:
                    category_transac = MapCategories(
                        category_name=category_item.strip(),
                        posted=timezone.now(),
                    )
                    category_transac.save()
                    category_id_list.append('_'+str(category_transac.id)+'_')
                else:
                    category_id_list.append('_'+str(category.id)+'_')
            map_data_ordered['categories'] = json.dumps(category_id_list)

        if line[0:11] == "Description":  # gone in MapFormat 9
            map_data_ordered['description'] = line[12:].strip().replace("'", "''")

        if line[0:7] == "MapSize":
            map_data_ordered['width'] = line[8:].strip().split(',')[0]
            map_data_ordered['height'] = line[8:].strip().split(',')[1]

        if line[0:6] == "Bounds":
            map_data_ordered['bounds'] = line[7:].strip()

        if line[0:9] == "MapFormat":
            map_data_ordered['mapformat'] = int(line[10:].strip())

        if line.strip()[-7:] == "mpspawn":
            expectspawn = True
        if line.strip()[0:8] == "Location":
            if expectspawn:
                spawnpoints += line.split(':')[1].strip()+","
                expectspawn = False

        if line.strip()[0:8] == "Playable":
            state = line.split(':')[1]
            if state.strip().lower() in ['true', 'on', 'yes', 'y']:
                map_data_ordered['players'] += 1

        if line[0:10] == "Visibility":
            if line[11:].strip() == "Shellmap":
                map_data_ordered['shellmap'] = True

        if line[0:7] == "Players":
            inPlayersBlock = True

        if line[0:6] == "Actors":
            inPlayersBlock = False

        if inPlayersBlock and line.strip() != "" and line[0:7] != "Players":
            map_data_ordered['base64_players'] += line[1:] + "\n"

        if line.strip()[0:5] == "Rules":  # for MapFormat < 10
            shouldCountRules = True
        if shouldCountRules:
            countAdvanced += 1

    map_data_ordered['spawnpoints'] = spawnpoints.rstrip(",")
    if countAdvanced > 16 and int(map_data_ordered['mapformat']) < 10:
        map_data_ordered['advanced'] = True

    if map_data_ordered['base64_players']:
        map_data_ordered['base64_players'] = base64.b64encode(map_data_ordered['base64_players'].encode()).decode()

    return {'response': map_data_ordered, 'error': False}


def ReadRules(item=False, fullpath="", parser=settings.OPENRA_VERSIONS[0], game_mod="ra"):
    if fullpath == "":
        if item is False:
            return {'data': '', 'error': True, 'response': 'wrong method call'}
        path = os.path.join(settings.BASE_DIR, 'openra', 'data', 'maps', str(item.id))
        Dir = os.listdir(path)
        for fn in Dir:
            if fn.endswith('.oramap'):
                fullpath = os.path.join(path, fn)
                break
        if fullpath == "":
            return {'data': '', 'error': True, 'response': 'could not find .oramap'}

    command = misc.build_utility_command(parser, game_mod, ['--map-rules', fullpath])
    proc = Popen(command.split(), stdout=PIPE).communicate()
    resp = {
        'data': base64.b64encode(proc[0]).decode(),
        'error': False,
        'response': 'fetched rules and base64 encoded',
        'advanced': False}
    if len(proc[0].decode().split("\n")) > 8:
        resp['advanced'] = True

    return resp


def UnzipMap(item, fullpath=""):
    if fullpath == "":
        path = os.path.join(settings.BASE_DIR, 'openra', 'data', 'maps', str(item.id))
        filename = ""
        Dir = os.listdir(path)
        for fn in Dir:
            if fn.endswith('.oramap'):
                filename = fn
                break
        if filename == "":
            print("failed to unzip %s" % item.id)
            return False
        fullpath = os.path.join(path, filename)

    z = zipfile.ZipFile(fullpath, mode='a')
    try:
        z.extractall(os.path.join(os.path.dirname(fullpath), 'content'))
    except:
        print("failed to unzip %s" % item.id)
        return False
    z.close()
    print('Unzipped map: %s' % item.id)
    return True


def LintCheck(item, fullpath="", parser=settings.OPENRA_VERSIONS[0], upgrade_with_new_rev=False):
    # this function performs a Lint Check for map
    response = {'error': True, 'response': ''}

    for current_parser in settings.OPENRA_VERSIONS:
        if upgrade_with_new_rev and current_parser != parser:
            continue

        if fullpath == "":
            path = os.path.join(settings.BASE_DIR, 'openra', 'data', 'maps', str(item.id))
            filename = ""
            Dir = os.listdir(path)
            for fn in Dir:
                if fn.endswith('.oramap'):
                    filename = fn
                    break
            if filename == "":
                print("error, can not find .oramap")
                response['error'] = True
                response['response'] = 'can not find .oramap'
                return response
            fullpath = os.path.join(path, filename)

        os.chmod(fullpath, 0o444)
        command = misc.build_utility_command(current_parser, item.game_mod, ['--check-yaml', fullpath])
        print(command)
        print('Started Lint check for parser: %s' % current_parser)
        proc = Popen(command.split(), stdout=PIPE).communicate()

        os.chmod(fullpath, 0o644)

        passing = True
        output_to_db = ""
        for res in proc:
            if res is None:
                continue
            lines = res.decode().split("\n")
            for line in lines:
                if 'Testing map' in line:
                    print(line)
                    passing = True
                else:
                    if line.strip() != "":
                        output_to_db += line + "\\n"
                        print(line)
                        passing = False

        if not upgrade_with_new_rev:
            lintObject = Lints.objects.filter(map_id=item.id, version_tag=current_parser)
            if lintObject:
                Lints.objects.filter(map_id=item.id, version_tag=current_parser).update(pass_status=passing, lint_output=output_to_db, posted=timezone.now())
            else:
                lint_transac = Lints(
                    item_type="maps",
                    map_id=item.id,
                    version_tag=current_parser,
                    pass_status=passing,
                    lint_output=output_to_db,
                    posted=timezone.now(),
                )
                lint_transac.save()

        if parser == current_parser:
            if passing:
                response['error'] = False
                response['response'] = 'pass_for_requested_parser'
                print('Lint check passed for requested parser: %s' % current_parser)
            else:
                print('Lint check failed for requested parser: %s' % current_parser)
        else:
            if passing:
                print('Lint check passed for parser: %s' % current_parser)
            else:
                print('Lint check failed for parser: %s' % current_parser)

    return response
