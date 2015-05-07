import shutil
import os
import zipfile
import string
import re
import signal
from subprocess import Popen, PIPE
import multiprocessing
from pgmagick import Image, ImageList, Geometry, FilterTypes, Blob

from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from openraData.models import Maps, Units, Mods, Screenshots
from openraData import utility, misc

class MapHandlers():
    
    def __init__(self, map_full_path_filename="", map_full_path_directory="", preview_filename=""):
        self.map_is_uploaded = False
        self.minimap_generated = False
        self.fullpreview_generated = False
        self.maphash = ""
        self.LintPassed = False
        self.advanced_map = False
        self.lua_map = False
        self.map_full_path_directory = map_full_path_directory
        self.map_full_path_filename = map_full_path_filename
        self.preview_filename = preview_filename
        self.currentDirectory = os.getcwd() + os.sep    # web root
        self.UID = False
        self.LOG = []
        self.legacy_name = ""
        self.legacy_map = False

        self.MapFormat = 6
        self.MapMod = ""
        self.MapTitle = ""
        self.MapAuthor = ""
        self.MapTileset = ""
        self.MapType = ""
        self.MapSize = ""
        self.MapDesc = ""
        self.MapPlayers = 0
        self.Bounds = ""
        self.spawnpoints = ""

    def ProcessUploading(self, user_id, f, post, rev=1, pre_r=0):
        
        parser = settings.OPENRA_VERSIONS['default']
        parser_to_db = parser
        if post.get("parser", None) != None:
            parser = post['parser']
            parser_to_db = parser
            if 'git' in parser:
                parser = settings.OPENRA_BLEED_PARSER

        if pre_r != 0:
            mapObject = Maps.objects.filter(id=pre_r, user_id=user_id)
            if not mapObject:
                self.LOG.append('Failed. You do not own map for which you want to upload a new revision.')
                return 'Failed. You do not own map for which you want to upload a new revision.'
            if mapObject[0].next_rev != 0:
                self.LOG.append('Failed. Unable to upload a new revision for map which already has one.')
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
        mimetype = proc[0].strip()
        if not ( mimetype == 'application/zip' and os.path.splitext(f.name)[1].lower() == '.oramap' ):
            if not ( mimetype == 'text/plain' and os.path.splitext(f.name)[1].lower() in ['.mpr', '.ini'] ):
                self.LOG.append('Failed. Unsupported file type.')
                return 'Failed. Unsupported file type.'

        name = f.name
        badChars = ": ; < > @ $ # & ( ) % '".split()
        for badchar in badChars:
            name = name.replace(badchar, "_")
        name = name.replace(" ", "_")
        # There can be weird chars still, if so: stop uploading
        findBadChars = re.findall(r'(\W+)', name)
        for bc in findBadChars:
            if bc not in ['.','-']:
                self.LOG.append('Failed. Your filename is bogus; rename and try again.')
                return 'Failed. Your filename is bogus; rename and try again.'

        if mimetype == 'text/plain':
            if not self.LegacyImport(tempname, parser):
                self.LOG.append('Failed to import legacy map.')
                misc.send_email_to_admin_OnMapFail(tempname)
                return 'Failed to import legacy map.'
            try:    # catch exception, TODO: remove after new release in 2015
                shutil.move(settings.OPENRA_ROOT_PATH + parser + "/" + self.legacy_name, tempname)
            except:
                pass
            name = os.path.splitext(name)[0] + '.oramap'
            self.legacy_map = True

        ### Check if user has already uploaded the same map
        self.GetHash(tempname, parser)
        userObject = User.objects.get(pk=user_id)
        try:
            hashExists = Maps.objects.get(user_id=userObject.id, map_hash=self.maphash)
            self.LOG.append("Failed. You've already uploaded this map.")
            self.UID = str(hashExists.id)
            return "Failed. You've already uploaded this map."
        except:
            pass   # all good

        ### Read Yaml ###
        read_yaml_response = utility.ReadYaml(False, tempname)
        resp_map_data = read_yaml_response['response']
        if read_yaml_response['error']:
            self.LOG.append(resp_map_data)
            misc.send_email_to_admin_OnMapFail(tempname)
            return resp_map_data

        ### Define license information
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


        ### Add record to Database
        transac = Maps(
            user = userObject,
            title = resp_map_data['title'],
            description = resp_map_data['description'],
            info = post['info'].strip(),
            author = resp_map_data['author'],
            map_type = resp_map_data['map_type'],
            players = resp_map_data['players'],
            game_mod = resp_map_data['game_mod'],
            map_hash = self.maphash.strip(),
            width = resp_map_data['width'],
            height = resp_map_data['height'],
            bounds = resp_map_data['bounds'],
            mapformat = resp_map_data['mapformat'],
            spawnpoints = resp_map_data['spawnpoints'],
            tileset = resp_map_data['tileset'],
            shellmap = resp_map_data['shellmap'],
            legacy_map = self.legacy_map,
            revision = rev,
            pre_rev = pre_r,
            next_rev = 0,
            downloading = True,
            requires_upgrade = not self.LintPassed,
            advanced_map = resp_map_data['advanced'],
            lua = resp_map_data['lua'],
            posted = timezone.now(),
            viewed = 0,
            policy_cc = cc,
            policy_commercial = commercial,
            policy_adaptations = adaptations,
            parser = parser_to_db,
        )
        transac.save()
        self.UID = str(transac.id)
        if pre_r != 0:
            Maps.objects.filter(id=pre_r).update(next_rev=transac.id)

        self.map_full_path_directory = self.currentDirectory + __name__.split('.')[0] + '/data/maps/' + self.UID + '/'
        if not os.path.exists(self.map_full_path_directory):
            os.makedirs(self.map_full_path_directory + 'content')
        self.map_full_path_filename = self.map_full_path_directory + name
        self.preview_filename = os.path.splitext(name)[0] + ".png"

        shutil.move(tempname, self.map_full_path_filename)

        self.map_is_uploaded = True
        self.flushLog( ['Map was successfully uploaded as "%s"' % name] )
        if post['info'] != "":
            self.flushLog( ['Info: ' + post['info']] )
        
        self.UnzipMap()
        self.LintCheck(resp_map_data['game_mod'], parser)
        if self.LintPassed:
            Maps.objects.filter(id=transac.id).update(requires_upgrade=False)
        else:
            Maps.objects.filter(id=transac.id).update(requires_upgrade=True)

        self.GenerateMinimap(resp_map_data['game_mod'], parser)
        #self.GenerateFullPreview(userObject, resp_map_data['game_mod'], parser)

        shp = multiprocessing.Process(target=self.GenerateSHPpreview, args=(resp_map_data['game_mod'], parser,), name='shppreview')
        shp.start()
        return False # no errors

    def UnzipMap(self):
        z = zipfile.ZipFile(self.map_full_path_filename, mode='a')
        try:
            z.extractall(self.map_full_path_directory + 'content/')
        except:
            pass
        z.close()

    def GetHash(self, filepath="", parser=settings.OPENRA_VERSIONS['default']):
        if filepath == "":
            filepath = self.map_full_path_filename

        os.chdir(settings.OPENRA_ROOT_PATH + parser + "/")

        command = 'mono --debug OpenRA.Utility.exe ra --map-hash ' + filepath
        proc = Popen(command.split(), stdout=PIPE).communicate()
        self.maphash = proc[0].strip()
        self.LOG.append(self.maphash)

        os.chdir(self.currentDirectory)

    def LintCheck(self, mod, parser=settings.OPENRA_VERSIONS['default']):
        os.chdir(settings.OPENRA_ROOT_PATH + parser + "/")

        command = 'mono --debug OpenRA.Utility.exe ' + mod + ' --check-yaml ' + self.map_full_path_filename

        proc = Popen(command.split(), stdout=PIPE).communicate()
        
        passing = True
        for res in proc:
            if res == None:
                continue
            lines = res.split("\n")
            for line in lines:
                if 'Testing map' in line:
                    passing = True
                else:
                    if line.strip() != "":
                        passing = False

        if passing:
            self.flushLog( ['Yaml check succeeded.'] )
            self.LintPassed = True
        else:
            self.flushLog(proc, "lint")
            self.flushLog( ['Yaml check failed.'] )

        os.chdir(self.currentDirectory)

    def GenerateMinimap(self, game_mod, parser=settings.OPENRA_VERSIONS['default']):
        os.chdir(settings.OPENRA_ROOT_PATH + parser + "/")

        command = 'mono --debug OpenRA.Utility.exe %s --map-preview %s' % (game_mod, self.map_full_path_filename)
        proc = Popen(command.split(), stdout=PIPE).communicate()

        try:
            shutil.move(misc.addSlash(settings.OPENRA_ROOT_PATH + parser + "/") + self.preview_filename,
                self.map_full_path_directory + os.path.splitext(self.preview_filename)[0] + "-mini.png")
            self.flushLog(proc)
            self.minimap_generated = True
        except:
            self.flushLog( ["Failed to generate minimap for this file."] )        

        os.chdir(self.currentDirectory)

    def GenerateFullPreview(self, userObject, game_mod, parser=settings.OPENRA_VERSIONS['default']):
        os.chdir(settings.OPENRA_ROOT_PATH, parser)

        command = 'mono --debug OpenRA.Utility.exe %s--full-preview %s' % (game_mod, self.map_full_path_filename)
        proc = Popen(command.split(), stdout=PIPE).communicate()

        try:
            shutil.move(misc.addSlash(settings.OPENRA_ROOT_PATH + parser + "/") + self.preview_filename,
                self.map_full_path_directory + os.path.splitext(self.preview_filename)[0] + "-full.png")
            self.flushLog(proc)
            self.fullpreview_generated = True
            transac = Screenshots(
                user = userObject,
                ex_id = int(self.UID),
                ex_name = "maps",
                posted =  timezone.now(),
                map_preview = True,
                )
            transac.save()
        except:
            self.flushLog( ["Failed to generate fullpreview for this file."] )

        os.chdir(self.currentDirectory)

    def GenerateSHPpreview(self, game_mod, parser=settings.OPENRA_VERSIONS['default']):
        Dir = os.listdir(self.map_full_path_directory+'content/')
        for fn in Dir:
            if fn.endswith('.shp'):
                os.mkdir(self.map_full_path_directory+'content/png/')
                os.chdir(self.map_full_path_directory+'content/png/')
                command = 'mono --debug %sOpenRA.Utility.exe %s --png %s %s' % (settings.OPENRA_ROOT_PATH + parser + "/", game_mod, self.map_full_path_directory+'content/'+fn, '../../../../palettes/0/RA1/temperat.pal')

                class TimedOut(Exception): # Raised if timed out.
                    pass

                def signal_handler(signum, frame):
                    raise TimedOut("Timed out!")

                signal.signal(signal.SIGALRM, signal_handler)

                signal.alarm(settings.UTILITY_TIME_LIMIT)    # Limit command execution time

                try:
                    proc = Popen(command.split(), stdout=PIPE).communicate()
                    self.flushLog(proc)
                    signal.alarm(0)
                except:
                    err = 'Error: failed to generate SHP preview for %s (map: %s)' % (fn, self.UID)
                    print(err)
                    misc.send_email_to_admin('ORC: Failed to generate SHP preview', '%s \n\n %s' % (err, command))

                    os.chdir(self.currentDirectory)
                    shutil.rmtree(self.map_full_path_directory+'content/png/')

                    continue
                pngsdir = os.listdir(self.map_full_path_directory+'content/png/')
                imglist = []
                for pngfn in pngsdir:
                    if pngfn.endswith('.png'):
                        imglist.append(pngfn)
                imglist.sort()
                imgs = ImageList()
                for img in imglist:
                    imgs.append(Image(self.map_full_path_directory+'content/png/'+img))
                imgs.animationDelayImages(50)
                imgs.writeImages(self.map_full_path_directory+'content/'+fn+'.gif')
                os.chdir(self.currentDirectory)
                shutil.rmtree(self.map_full_path_directory+'content/png/')

    def LegacyImport(self, mapPath, parser=settings.OPENRA_VERSIONS['default']):
        os.chdir(settings.OPENRA_ROOT_PATH + parser + "/")
        for mod in ['ra','cnc','d2k','ts']:
            command = 'mono --debug OpenRA.Utility.exe %s --map-import %s' % (mod, mapPath)
            proc = Popen(command.split(), stdout=PIPE).communicate()
            self.LOG.append([proc[0]])
            if "Error" in proc[0] or "Unknown" in proc[0]:
                continue
            else:
                if "saved" in proc[0]:
                    self.legacy_name = proc[0].split(' saved')[0]
                    os.chdir(self.currentDirectory)
                    return True
                else:
                    continue
        os.chdir(self.currentDirectory)
        return False

    def flushLog(self, output=[], lint=""):
        logfile = open(self.map_full_path_directory + lint + "log", "a")
        for line in output:
            if line != None:
                logfile.write(line.strip() + "\n")
                if lint == "":
                    self.LOG.append(line.strip())
        logfile.close()
        return True

def addScreenshot(f, arg, user_id, item):
    if item == 'map':
        Object = Maps.objects.filter(id=arg)
        if not Object:
            return False
        if not (Object[0].user_id == user_id.id or user_id.is_superuser):
            return False
    else:
        return False
    tempname = '/tmp/screenshot.temp'
    with open(tempname, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

    command = 'file -b --mime-type %s' % tempname
    proc = Popen(command.split(), stdout=PIPE).communicate()
    mimetype = proc[0].strip()
    if mimetype not in ['image/jpeg','image/png','image/gif']:
        return False

    userObject = User.objects.get(pk=Object[0].user_id)
    transac = Screenshots(
        user = userObject,
        ex_id = int(arg),
        ex_name = item+"s",
        posted =  timezone.now(),
        map_preview = False,
        )
    transac.save()

    path = os.getcwd() + os.sep + __name__.split('.')[0] + '/data/screenshots/' + str(transac.id) + '/'
    if not os.path.exists(path):
        os.makedirs(path)

    shutil.move(tempname, path + arg + "." + mimetype.split('/')[1])

    command = 'identify -format "%w,%h" {0}'.format(path + arg + "." + mimetype.split('/')[1])
    proc = Popen(command.split(), stdout=PIPE).communicate()
    details = proc[0].strip().strip('"').split(',')

    im = Image(Blob(open(path + arg + "." + mimetype.split('/')[1]).read()), Geometry(int(details[0]),int(details[1])))
    
    scaleH = int(details[0]) / 100.0
    scaleH = 250 / scaleH
    scaleH = int(details[1]) / 100.0 * scaleH

    im.quality(100)
    im.filterType(FilterTypes.SincFilter)
    im.scale('250x%s' % scaleH)
    im.sharpen(1.0)
    im.write(str(path + arg + "-mini." + mimetype.split('/')[1]))
