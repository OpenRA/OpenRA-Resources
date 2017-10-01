import os
import shutil
import zipfile
import string
import random
import signal
import json
import base64
import time
import multiprocessing
from subprocess import Popen, PIPE
from django.conf import settings
from django.utils import timezone
from openra.models import Maps, Lints, MapCategories
from openra import misc


def map_upgrade(mapObject, engine, parser=list(reversed(list(settings.OPENRA_VERSIONS.values())))[0], new_rev_on_upgrade=True, upgrade_if_hash_matches=False, upgrade_if_lint_fails=False):

    parser_to_db = parser
    parser = settings.OPENRA_ROOT_PATH + parser

    currentDirectory = os.getcwd() + os.sep

    upgraded_maps = []

    for item in mapObject:

        os.chdir(parser + "/")

        if item.next_rev != 0:
            print('Aborting upgrade of map: %s, as it is not the latest revision' % (item.id))
            print("Interrupted map upgrade: %s" % (item.id))
            continue

        path = currentDirectory + 'openra/data/maps/' + str(item.id) + '/'
        filename = ""
        Dir = os.listdir(path)
        for fn in Dir:
            if fn.endswith('.oramap'):
                filename = fn
                break
        if filename == "":
            print("error, can not find .oramap")
            print("Interrupted map upgrade: %s" % (item.id))
            continue

        # Copy map to temporarily location
        ora_temp_dir_name = '/tmp/openra_resources/' + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8)) + "/"
        os.makedirs(ora_temp_dir_name)

        shutil.copy(path+filename, ora_temp_dir_name)

        if_new_rev = "WITH creating new revision"
        if not new_rev_on_upgrade:
            if_new_rev = "WITHOUT creating new revision"

        print('\nStarting map upgrade action %s on map: %s. Using parser: %s' % (if_new_rev, item.id, parser_to_db))
        print('All operations are performed in temporarily location until success: %s' % ora_temp_dir_name)
        ###

        if item.parser != "":
            if 'git' not in item.parser:
                parser_eng = item.parser.split('-')[1]
                if int(engine) > int(parser_eng):
                    engine = parser_eng

        command = 'mono --debug OpenRA.Utility.exe %s --upgrade-map %s %s' % (item.game_mod, ora_temp_dir_name+filename, engine)
        print(command)
        proc = Popen(command.split(), stdout=PIPE).communicate()

        upgraded = True
        for line in proc:
            if line is None:
                continue
            if 'Converted' in line.decode() and 'MapFormat' in line.decode():
                continue
            if line.decode().strip() != "":
                upgraded = False

        os.chdir(currentDirectory)

        if not upgraded:
            print("Problems upgrading map: %s" % (item.id))
            print("Interrupted map upgrade: %s" % (item.id))

            if os.path.isdir(ora_temp_dir_name):
                shutil.rmtree(ora_temp_dir_name)

            continue

        recalculate_hash_response = recalculate_hash(item, ora_temp_dir_name+filename, parser)
        if recalculate_hash_response['error']:
            print("Interrupted map upgrade: %s" % (item.id))

            if os.path.isdir(ora_temp_dir_name):
                shutil.rmtree(ora_temp_dir_name)

            continue
        if recalculate_hash_response['maphash'] == item.map_hash and upgrade_if_hash_matches is False:
            print("Upgrade is not required, map hash after running `--upgrade-map` is idetical to original: %s" % (item.id))
            print("Interrupted map upgrade: %s" % (item.id))

            if os.path.isdir(ora_temp_dir_name):
                shutil.rmtree(ora_temp_dir_name)

            continue

        lint_check_response = LintCheck(item, ora_temp_dir_name+filename, parser, new_rev_on_upgrade)
        if lint_check_response['error'] is True or lint_check_response['response'] != 'pass_for_requested_parser':
            if upgrade_if_lint_fails is False:
                print("Lint check failed for requested parser: %s" % parser_to_db)
                print("Interrupted map upgrade: %s" % (item.id))

                if os.path.isdir(ora_temp_dir_name):
                    shutil.rmtree(ora_temp_dir_name)

                continue
        if_map_requires_upgrade = True
        if lint_check_response['error'] is False and lint_check_response['response'] == 'pass_for_requested_parser':
            if_map_requires_upgrade = False

        unzipped_map = UnzipMap(item, ora_temp_dir_name+filename)
        if not unzipped_map:
            print("Interrupted map upgrade: %s" % (item.id))

            if os.path.isdir(ora_temp_dir_name):
                shutil.rmtree(ora_temp_dir_name)

            continue

        # Read Yaml
        read_yaml_response = ReadYaml(item, ora_temp_dir_name+filename)

        resp_map_data = read_yaml_response['response']
        if read_yaml_response['error']:
            print("ReadYaml: " + resp_map_data)
            print("Interrupted map upgrade: %s" % (item.id))

            if os.path.isdir(ora_temp_dir_name):
                shutil.rmtree(ora_temp_dir_name)

            continue

        # Read Rules
        base64_rules = {}
        base64_rules['data'] = ''
        base64_rules['advanced'] = resp_map_data['advanced']
        if int(resp_map_data['mapformat']) >= 10:
            base64_rules = ReadRules(item, ora_temp_dir_name+filename, parser, item.game_mod)
            print(base64_rules['response'])
        if base64_rules['advanced']:
            resp_map_data['advanced'] = True

        if upgraded and recalculate_hash_response['error'] is False and unzipped_map and read_yaml_response['error'] is False:

            if not new_rev_on_upgrade:
                # copy directory tree from temporarily location to old location
                misc.copytree(ora_temp_dir_name, path)

                Maps.objects.filter(id=item.id).update(map_hash=recalculate_hash_response['maphash'])
                Maps.objects.filter(id=item.id).update(requires_upgrade=if_map_requires_upgrade)

                Maps.objects.filter(id=item.id).update(game_mod=resp_map_data['game_mod'])
                Maps.objects.filter(id=item.id).update(title=resp_map_data['title'])
                Maps.objects.filter(id=item.id).update(author=resp_map_data['author'])
                Maps.objects.filter(id=item.id).update(tileset=resp_map_data['tileset'])
                Maps.objects.filter(id=item.id).update(map_type=resp_map_data['map_type'])
                Maps.objects.filter(id=item.id).update(categories=resp_map_data['categories'])
                Maps.objects.filter(id=item.id).update(description=resp_map_data['description'])
                Maps.objects.filter(id=item.id).update(players=resp_map_data['players'])
                Maps.objects.filter(id=item.id).update(bounds=resp_map_data['bounds'])
                Maps.objects.filter(id=item.id).update(mapformat=resp_map_data['mapformat'])
                Maps.objects.filter(id=item.id).update(spawnpoints=resp_map_data['spawnpoints'])
                Maps.objects.filter(id=item.id).update(width=resp_map_data['width'])
                Maps.objects.filter(id=item.id).update(height=resp_map_data['height'])
                Maps.objects.filter(id=item.id).update(shellmap=resp_map_data['shellmap'])
                Maps.objects.filter(id=item.id).update(base64_rules=base64_rules['data'])
                Maps.objects.filter(id=item.id).update(base64_players=resp_map_data['base64_players'])
                Maps.objects.filter(id=item.id).update(lua=resp_map_data['lua'])
                Maps.objects.filter(id=item.id).update(advanced_map=resp_map_data['advanced'])
                Maps.objects.filter(id=item.id).update(parser=parser_to_db)

                if resp_map_data['mapformat'] >= 9: # Description is gone in MapFormat 9
                    if item.description:
                        new_info = item.description+'\n\n'+item.info
                    else:
                        new_info = item.info
                    Maps.objects.filter(id=item.id).update(info=new_info)

                print('Updated data, fetched from Yaml: %s' % item.id)

                print('Finished upgrading map %s: %s \n' % (if_new_rev, item.id))
                upgraded_maps.append(item.id)
            else:
                time.sleep(1)
                # create new revision after successfully upgrading map in temporarily location

                rev = item.revision + 1

                transac = Maps(
                    user=item.user,
                    title=resp_map_data['title'],
                    description=resp_map_data['description'],
                    info=item.info,
                    author=resp_map_data['author'],
                    map_type=resp_map_data['map_type'],
                    categories=resp_map_data['categories'],
                    players=resp_map_data['players'],
                    game_mod=resp_map_data['game_mod'],
                    map_hash=recalculate_hash_response['maphash'],
                    width=resp_map_data['width'],
                    height=resp_map_data['height'],
                    bounds=resp_map_data['bounds'],
                    mapformat=resp_map_data['mapformat'],
                    spawnpoints=resp_map_data['spawnpoints'],
                    tileset=resp_map_data['tileset'],
                    shellmap=resp_map_data['shellmap'],
                    base64_rules=base64_rules['data'],
                    base64_players=resp_map_data['base64_players'],
                    legacy_map=False,
                    revision=rev,
                    pre_rev=item.id,
                    next_rev=0,
                    downloading=True,
                    requires_upgrade=if_map_requires_upgrade,
                    advanced_map=resp_map_data['advanced'],
                    lua=resp_map_data['lua'],
                    posted=item.posted,   # we do not want to break order of maps, so we save old date for new rev
                    viewed=0,
                    policy_cc=item.policy_cc,
                    policy_commercial=item.policy_commercial,
                    policy_adaptations=item.policy_adaptations,
                    parser=parser_to_db,
                )
                transac.save()
                Maps.objects.filter(id=item.id).update(next_rev=transac.id)

                if resp_map_data['mapformat'] >= 9:  # Description is gone in MapFormat 9
                    if item.description:
                        new_info = item.description+'\n\n'+item.info
                    else:
                        new_info = item.info
                    Maps.objects.filter(id=transac.id).update(info=new_info)

                new_path = currentDirectory + 'openra/data/maps/' + str(transac.id) + '/'
                if not os.path.exists(new_path):
                    os.makedirs(new_path + 'content')

                misc.copytree(path, new_path)
                misc.copytree(ora_temp_dir_name, new_path)

                print('Finished upgrading map %s %s. New ID: %s \n' % (item.id, if_new_rev, transac.id))
                upgraded_maps.append(transac.id)

                print("\nRunning Lint checks for successfully upgraded map\n")
                LintCheck(transac, "", parser)

                print("\nRunning SHPtoGIF generator, in case there are SHP files\n")
                #shp = multiprocessing.Process(target=GenerateSHPpreview, args=(item, parser,), name='SHPtoGIF')
                #shp.start()

            if os.path.isdir(ora_temp_dir_name):
                shutil.rmtree(ora_temp_dir_name)

    os.chdir(currentDirectory)
    return upgraded_maps


def recalculate_hash(item, fullpath="", parser=settings.OPENRA_ROOT_PATH + list(reversed(list(settings.OPENRA_VERSIONS.values())))[0]):

    currentDirectory = os.getcwd() + os.sep
    os.chdir(parser + "/")

    if fullpath == "":

        path = currentDirectory + 'openra/data/maps/' + str(item.id) + '/'
        filename = ""
        Dir = os.listdir(path)
        for fn in Dir:
            if fn.endswith('.oramap'):
                filename = fn
                break
        if filename == "":
            os.chdir(currentDirectory)
            print('Failed to recalculate hash for %s: %s' % (item.id, 'can not find map'))
            return {'response': 'can not find map', 'error': True, 'maphash': 'none'}
        fullpath = path + filename

    os.chmod(fullpath, 0o444)

    command = 'mono --debug OpenRA.Utility.exe %s --map-hash %s' % (item.game_mod, fullpath)
    proc = Popen(command.split(), stdout=PIPE).communicate()

    os.chmod(fullpath, 0o644)

    maphash = proc[0].decode().strip()
    os.chdir(currentDirectory)
    print('Recalculated hash: %s' % item.id)

    return {'response': 'success', 'error': False, 'maphash': maphash}


def ReadYaml(item=False, fullpath=""):
    if fullpath == "":
        if item is False:
            return {'response': 'wrong method call', 'error': True}
        currentDirectory = os.getcwd() + os.sep
        path = currentDirectory + 'openra/data/maps/' + str(item.id) + '/'
        Dir = os.listdir(path)
        for fn in Dir:
            if fn.endswith('.oramap'):
                fullpath = path + fn
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


def ReadRules(item=False, fullpath="", parser=settings.OPENRA_ROOT_PATH + list(reversed(list(settings.OPENRA_VERSIONS.values())))[0], game_mod="ra"):

    currentDirectory = os.getcwd() + os.sep
    os.chdir(parser + "/")

    if fullpath == "":
        if item is False:
            return {'data': '', 'error': True, 'response': 'wrong method call'}
        path = currentDirectory + 'openra/data/maps/' + str(item.id) + '/'
        Dir = os.listdir(path)
        for fn in Dir:
            if fn.endswith('.oramap'):
                fullpath = path + fn
                break
        if fullpath == "":
            return {'data': '', 'error': True, 'response': 'could not find .oramap'}

    command = 'mono --debug OpenRA.Utility.exe %s --map-rules %s' % (game_mod, fullpath)
    proc = Popen(command.split(), stdout=PIPE).communicate()
    resp = {
        'data': base64.b64encode(proc[0]).decode(),
        'error': False,
        'response': 'fetched rules and base64 encoded',
        'advanced': False}
    if len(proc[0].decode().split("\n")) > 8:
        resp['advanced'] = True

    os.chdir(currentDirectory)
    return resp


def UnzipMap(item, fullpath=""):
    if fullpath == "":
        currentDirectory = os.getcwd() + os.sep
        path = currentDirectory + 'openra/data/maps/' + str(item.id) + '/'
        filename = ""
        Dir = os.listdir(path)
        for fn in Dir:
            if fn.endswith('.oramap'):
                filename = fn
                break
        if filename == "":
            print("failed to unzip %s" % item.id)
            return False
        fullpath = path + filename

    z = zipfile.ZipFile(fullpath, mode='a')
    try:
        z.extractall(os.path.dirname(fullpath) + '/content/')
    except:
        print("failed to unzip %s" % item.id)
        return False
    z.close()
    print('Unzipped map: %s' % item.id)
    return True


def LintCheck(item, fullpath="", parser=settings.OPENRA_ROOT_PATH + list(reversed(list(settings.OPENRA_VERSIONS.values())))[0], upgrade_with_new_rev=False):
    # this function performs a Lint Check for map
    response = {'error': True, 'response': ''}

    currentDirectory = os.getcwd() + os.sep

    available_parsers = list(reversed(list(settings.OPENRA_VERSIONS.values())))

    for current_parser in available_parsers:
        if current_parser == "bleed":

            bleed_tag = None
            if (settings.OPENRA_BLEED_HASH_FILE_PATH != '' and os.path.isfile(settings.OPENRA_BLEED_HASH_FILE_PATH)):
                bleed_tag = open(settings.OPENRA_BLEED_HASH_FILE_PATH, 'r')
                bleed_tag = 'git-' + bleed_tag.readline().strip()[0:7]
            if bleed_tag is None:
                continue

            if not os.path.isfile(settings.OPENRA_BLEED_PARSER + 'OpenRA.Utility.exe'):
                continue

            current_parser_to_db = bleed_tag
            current_parser_path = settings.OPENRA_BLEED_PARSER
        else:
            current_parser_to_db = current_parser
            current_parser_path = settings.OPENRA_ROOT_PATH + current_parser

        if upgrade_with_new_rev and current_parser_path != parser:
            continue

        os.chdir(current_parser_path + "/")

        if fullpath == "":
            path = currentDirectory + 'openra/data/maps/' + str(item.id) + '/'
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
            fullpath = path + filename

        os.chmod(fullpath, 0o444)

        command = 'mono --debug OpenRA.Utility.exe ' + item.game_mod.lower() + ' --check-yaml ' + fullpath
        print(command)
        print('Started Lint check for parser: %s' % current_parser_to_db)
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
            lintObject = Lints.objects.filter(map_id=item.id, version_tag=current_parser_to_db)
            lintObjectGit = Lints.objects.filter(map_id=item.id, version_tag__startswith='git')
            if lintObject:
                Lints.objects.filter(map_id=item.id, version_tag=current_parser_to_db).update(pass_status=passing, lint_output=output_to_db, posted=timezone.now())
            elif lintObjectGit and current_parser_to_db.startswith('git'):
                Lints.objects.filter(map_id=item.id, version_tag__startswith='git').update(pass_status=passing, lint_output=output_to_db, posted=timezone.now())
            else:
                lint_transac = Lints(
                    item_type="maps",
                    map_id=item.id,
                    version_tag=current_parser_to_db,
                    pass_status=passing,
                    lint_output=output_to_db,
                    posted=timezone.now(),
                )
                lint_transac.save()

        if parser == current_parser_path:
            if passing:
                response['error'] = False
                response['response'] = 'pass_for_requested_parser'
                print('Lint check passed for requested parser: %s' % current_parser_to_db)
            else:
                print('Lint check failed for requested parser: %s' % current_parser_to_db)
        else:
            if passing:
                print('Lint check passed for parser: %s' % current_parser_to_db)
            else:
                print('Lint check failed for parser: %s' % current_parser_to_db)

        os.chdir(currentDirectory)
    return response


def GenerateSHPpreview(item, parser=settings.OPENRA_ROOT_PATH + list(reversed(list(settings.OPENRA_VERSIONS.values())))[0]):
    # generates gif preview of shp files for every mapObject in list of objects
    currentDirectory = os.getcwd()

    path = os.getcwd() + os.sep + 'openra/data/maps/' + str(item.id) + os.sep
    Dir = os.listdir(path + 'content/')
    if os.path.isdir(path+'content/png/'):
        shutil.rmtree(path+'content/png/')
    for fn in Dir:
        if fn.endswith('.shp'):
            os.mkdir(path + 'content/png/')
            os.chdir(path + 'content/png/')
            command = 'mono --debug %sOpenRA.Utility.exe %s --png %s %s' % (parser + "/", item.game_mod, path+'content/'+fn, '../../../../palettes/0/RA1/temperat.pal')
            print(command)

            class TimedOut(Exception):  # Raised if timed out.
                pass

            def signal_handler(signum, frame):
                raise TimedOut("Timed out!")

            signal.signal(signal.SIGALRM, signal_handler)

            signal.alarm(settings.UTILITY_TIME_LIMIT)    # Limit command execution time

            try:
                proc = Popen(command.split(), stdout=PIPE).communicate()
                signal.alarm(0)
            except:
                err = 'Error: failed to generate SHP preview for %s (map: %s)' % (fn, item.id)
                print(err)
                misc.send_email_to_admin('ORC: Failed to generate SHP preview', '%s \n\n %s' % (err, command))

                os.chdir(currentDirectory)
                shutil.rmtree(path+'content/png/')

                continue

            convert_command = 'convert -delay 50 -loop 1 '+path+'content/png/*.png %s' % (path+'content/'+fn+'.gif')
            convert_proc = Popen(convert_command.split(), stdout=PIPE).communicate()

            os.chdir(currentDirectory)
            shutil.rmtree(path+'content/png/')
    return True


def GenerateMinimap(item, parser=settings.OPENRA_ROOT_PATH + list(reversed(list(settings.OPENRA_VERSIONS.values())))[0]):

    if int(item.mapformat) >= 10:
        print('MapFormat 10 and newer does not support generating minimap. Using included map.png instead.')
        return False

    currentDirectory = os.getcwd() + os.sep

    os.chdir(parser + "/")

    path = currentDirectory + 'openra/data/maps/' + str(item.id) + os.sep
    filename = ""
    Dir = os.listdir(path)
    for fn in Dir:
        if fn.endswith('.oramap'):
            filename = fn
            break
    if filename == "":
        os.chdir(currentDirectory)
        return False

    os.chmod(path + filename, 0o444)
    command = 'mono --debug OpenRA.Utility.exe %s --map-preview %s' % (item.game_mod, path + filename)
    print(command)
    proc = Popen(command.split(), stdout=PIPE).communicate()
    os.chmod(path + filename, 0o644)
    try:
        shutil.move(parser + "/" + os.path.splitext(filename)[0] + ".png", path + os.path.splitext(filename)[0] + "-mini.png")
        os.chdir(currentDirectory)
        print('Minimap generated: %s' % item.id)
        return True
    except:
        os.chdir(currentDirectory)
        print('Failed to generate minimap: %s' % item.id)
        return False
