import shutil
import os
import zipfile
import string
import re
import signal
import random
import yaml
import json
from subprocess import Popen, PIPE
import multiprocessing

from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from openra.models import Maps, Lints, Screenshots
from openra import utility, misc


class MapHandlers():

    def __init__(self, map_full_path_filename="", map_full_path_directory="", preview_filename=""):
        self.minimap_generated = False
        self.maphash = ""
        self.LintPassed = False
        self.map_full_path_directory = map_full_path_directory
        self.map_full_path_filename = map_full_path_filename
        self.preview_filename = preview_filename
        self.currentDirectory = settings.BASE_DIR    # web root
        self.UID = False
        self.legacy_name = ""
        self.legacy_map = False

    def ProcessUploading(self, user_id, f, post, rev=1, pre_r=0):

        parser_to_db = list(reversed(list(settings.OPENRA_VERSIONS.values())))[0]  # default parser = the latest
        parser = os.path.join(settings.OPENRA_ROOT_PATH, parser_to_db)

        if post.get("parser", None) is not None:
            parser_to_db = post['parser']
            parser = os.path.join(settings.OPENRA_ROOT_PATH, parser_to_db)
            if 'git' in parser:
                parser = settings.OPENRA_BLEED_PARSER

        if pre_r != 0:
            mapObject = Maps.objects.filter(id=pre_r, user_id=user_id)
            if not mapObject:
                return 'Failed. You do not own map for which you want to upload a new revision.'
            if mapObject[0].next_rev != 0:
                return 'Failed. Unable to upload a new revision for map which already has one.'
            previous_policy_cc = mapObject[0].policy_cc
            previous_policy_commercial = mapObject[0].policy_commercial
            previous_policy_adaptations = mapObject[0].policy_adaptations
        tempname = '/tmp/openramap.oramap'
        with open(tempname, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)

        command = 'file -b --mime-type %s' % tempname
        proc = Popen(command.split(), stdout=PIPE).communicate()
        mimetype = proc[0].decode().strip()
        if not (mimetype == 'application/zip' and os.path.splitext(f.name)[1].lower() == '.oramap'):
            if not (mimetype == 'text/plain' and os.path.splitext(f.name)[1].lower() in ['.mpr', '.ini']):
                return 'Failed. Unsupported file type.'

        name = f.name
        badChars = ": ; < > @ $ # & ( ) % '".split()
        for badchar in badChars:
            name = name.replace(badchar, "_")
        name = name.replace(" ", "_")
        # There can be weird chars still, if so: stop uploading
        findBadChars = re.findall(r'(\W+)', name)
        for bc in findBadChars:
            if bc not in ['.', '-']:
                return 'Failed. Your filename is bogus; rename and try again.'

        if mimetype == 'text/plain':
            if not self.LegacyImport(tempname, parser):
                misc.send_email_to_admin_OnMapFail(tempname)
                return 'Failed to import legacy map.'
            shutil.move(self.legacy_name, tempname)
            name = os.path.splitext(name)[0] + '.oramap'
            self.legacy_map = True

        # Check if user has already uploaded the same map
        self.GetHash(tempname, parser)
        if 'Converted' in self.maphash and 'to MapFormat' in self.maphash:
            misc.send_email_to_admin_OnMapFail(tempname)
            return 'Failed to upload with this parser. MapFormat does not match. Try to upgrade your map or use different parser.'

        userObject = User.objects.get(pk=user_id)
        try:
            hashExists = Maps.objects.get(user_id=userObject.id, map_hash=self.maphash)
            self.UID = str(hashExists.id)
            return "Failed. You've already uploaded this map."
        except:
            pass   # all good

        # Read Yaml
        read_yaml_response = utility.ReadYaml(False, tempname)
        resp_map_data = read_yaml_response['response']
        if read_yaml_response['error']:
            misc.send_email_to_admin_OnMapFail(tempname)
            return resp_map_data

        if int(resp_map_data['mapformat']) < 10:
            misc.send_email_to_admin_OnMapFail(tempname)
            return "Unable to import maps older than map format 10."

        # Read Rules
        base64_rules = utility.ReadRules(False, tempname, parser, resp_map_data['game_mod'])
        if (base64_rules['error']):
            print(base64_rules['response'])

        if base64_rules['advanced']:
            resp_map_data['advanced'] = True

        # Define license information
        cc = False
        commercial = False
        adaptations = ""
        if pre_r == 0:
            if post['policy_cc'] == 'cc_yes':
                cc = True
                if post['commercial'] == "com_yes":
                    commercial = True
                if post['adaptations'] == "adapt_yes":
                    adaptations = "yes"
                elif post['adaptations'] == "adapt_no":
                    adaptations = "no"
                else:
                    adaptations = "yes and shared alike"
        else:
            cc = previous_policy_cc
            commercial = previous_policy_commercial
            adaptations = previous_policy_adaptations


        # Add record to Database
        transac = Maps(
            user=userObject,
            title=resp_map_data['title'],
            description=resp_map_data['description'],
            info=post['info'].strip(),
            author=resp_map_data['author'],
            map_type=resp_map_data['map_type'],
            categories=resp_map_data['categories'],
            players=resp_map_data['players'],
            game_mod=resp_map_data['game_mod'],
            map_hash=self.maphash.strip(),
            width=resp_map_data['width'],
            height=resp_map_data['height'],
            bounds=resp_map_data['bounds'],
            mapformat=resp_map_data['mapformat'],
            spawnpoints=resp_map_data['spawnpoints'],
            tileset=resp_map_data['tileset'],
            shellmap=resp_map_data['shellmap'],
            base64_rules=base64_rules['data'],
            base64_players=resp_map_data['base64_players'],
            legacy_map=self.legacy_map,
            revision=rev,
            pre_rev=pre_r,
            next_rev=0,
            downloading=True,
            requires_upgrade=True,
            advanced_map=resp_map_data['advanced'],
            lua=resp_map_data['lua'],
            posted=timezone.now(),
            viewed=0,
            policy_cc=cc,
            policy_commercial=commercial,
            policy_adaptations=adaptations,
            parser=parser_to_db,
        )
        transac.save()
        self.UID = str(transac.id)

        self.map_full_path_directory = os.path.join(self.currentDirectory, __name__.split('.')[0], 'data', 'maps', self.UID)

        try:
            if not os.path.exists(self.map_full_path_directory):
                os.makedirs(os.path.join(self.map_full_path_directory, 'content'))
        except Exception as e:
            print("Failed to create directory for new map", self.map_full_path_directory)
            transac.delete() # Remove failed map from DB before raise
            raise

        if pre_r != 0:
            Maps.objects.filter(id=pre_r).update(next_rev=transac.id)

        self.map_full_path_filename = os.path.join(self.map_full_path_directory, name)
        self.preview_filename = os.path.splitext(name)[0] + ".png"

        shutil.move(tempname, self.map_full_path_filename)

        self.UnzipMap()

        lint_check_response = utility.LintCheck(transac, self.map_full_path_filename, parser)
        if lint_check_response['error'] is False and lint_check_response['response'] == 'pass_for_requested_parser':
            self.LintPassed = True

        if self.LintPassed:
            Maps.objects.filter(id=transac.id).update(requires_upgrade=False)
        else:
            Maps.objects.filter(id=transac.id).update(requires_upgrade=True)


        print("--- New map: %s" % self.UID)
        return False  # no errors

    def UnzipMap(self):
        z = zipfile.ZipFile(self.map_full_path_filename, mode='a')
        try:
            z.extractall(os.path.join(self.map_full_path_directory, 'content'))
        except:
            pass
        z.close()

    def GetHash(self, filepath="", parser=settings.OPENRA_ROOT_PATH + list(reversed(list(settings.OPENRA_VERSIONS.values())))[0]):
        if filepath == "":
            filepath = self.map_full_path_filename

        os.chmod(filepath, 0o444)

        command = 'mono --debug %s ra --map-hash %s' % (os.path.join(parser, 'OpenRA.Utility.exe'), filepath)
        proc = Popen(command.split(), stdout=PIPE).communicate()

        os.chmod(filepath, 0o644)

        self.maphash = proc[0].decode().strip()

    def GenerateMinimap(self, game_mod, parser=settings.OPENRA_ROOT_PATH + list(reversed(list(settings.OPENRA_VERSIONS.values())))[0]):

        os.chmod(self.map_full_path_filename, 0o444)
        command = 'mono --debug %s %s --map-preview %s' % (os.path.join(parser, 'OpenRA.Utility.exe'), game_mod, self.map_full_path_filename)
        proc = Popen(command.split(), stdout=PIPE).communicate()
        os.chmod(self.map_full_path_filename, 0o644)

        try:
            shutil.move(
                os.path.join(parser, self.preview_filename),
                os.path.join(self.map_full_path_directory, os.path.splitext(self.preview_filename)[0] + "-mini.png"))
            self.minimap_generated = True
        except:
            pass  # failed to generate minimap

    def LegacyImport(self, mapPath, parser=settings.OPENRA_ROOT_PATH + list(reversed(list(settings.OPENRA_VERSIONS.values())))[0]):
        for mod in ['ra', 'cnc']:

            assign_mod = mod
            if mod == 'cnc':
                assign_mod = 'td'

            pre_command = 'mono --debug %s ra' % (os.path.join(parser, 'OpenRA.Utility.exe'))
            pre_proc = Popen(pre_command.split(), stdout=PIPE).communicate()
            if '--import-' in pre_proc[0].decode():
                command = 'mono --debug %s %s --import-%s-map %s' % (os.path.join(parser, 'OpenRA.Utility.exe'), mod, assign_mod, mapPath)
            else:
                command = 'mono --debug %s %s --map-import %s' % (os.path.join(parser, 'OpenRA.Utility.exe'), mod, mapPath)

            proc = Popen(command.split(), stdout=PIPE).communicate()

            if "Error" in proc[0].decode():
                continue
            else:
                if "saved" in proc[0].decode():
                    self.legacy_name = proc[0].decode().split("\n")[-2].split(' saved')[0]
                    return True
                else:
                    continue
        return False


def addScreenshot(request, arg, item):
    if item == 'map':
        Object = Maps.objects.filter(id=arg)
        if not Object:
            return False
        if not (Object[0].user_id == request.user.id or request.user.is_superuser):
            return False
    else:
        return False
    tempname = '/tmp/screenshot.temp'
    with open(tempname, 'wb+') as destination:
        for chunk in request.FILES['screenshot'].chunks():
            destination.write(chunk)

    command = 'file -b --mime-type %s' % tempname
    proc = Popen(command.split(), stdout=PIPE).communicate()
    mimetype = proc[0].decode().strip()
    if mimetype not in ['image/jpeg', 'image/png', 'image/gif']:
        return False

    map_preview = False
    preview = request.POST.get('map_preview', None)
    if preview == 'on':
        map_preview = True

    transac = Screenshots(
        user=Object[0].user,
        ex_id=int(arg),
        ex_name=item+"s",
        posted=timezone.now(),
        map_preview=map_preview,
        )
    transac.save()

    path = os.path.join(settings.BASE_DIR, __name__.split('.')[0], 'data', 'screenshots', str(transac.id))
    if not os.path.exists(path):
        os.makedirs(path)

    sc_full_name = os.path.join(path, arg + "." + mimetype.split('/')[1])
    sc_mini_name = os.path.join(path, arg + "-mini." + mimetype.split('/')[1])

    shutil.move(tempname, sc_full_name)

    command = 'convert -resize 250x -quality 100 -sharpen 1.0 %s %s' % (sc_full_name, sc_mini_name)
    proc = Popen(command.split(), stdout=PIPE).communicate()
