import shutil
import os
import zipfile
import string
import re
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
        if pre_r != 0:
            mapObject = Maps.objects.filter(id=pre_r, user_id=user_id)
            if not mapObject:
                self.LOG.append('Failed. You do not own map for which you want to upload a new revision.')
                return False
            if mapObject[0].next_rev != 0:
                self.LOG.append('Failed. Unable to upload a new revision for map which already has one')
                return False
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
        if not (mimetype == 'application/zip' and os.path.splitext(f.name)[1].lower() == '.oramap'):
            if not (mimetype == 'text/plain' and os.path.splitext(f.name)[1].lower() == '.mpr'):
                self.LOG.append('Failed. Unsupported file type.')
                return False

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
                return False

        if mimetype == 'text/plain':
            if not self.LegacyImport(tempname):
                self.LOG.append('Failed to import legacy map.')
                misc.send_email_to_admin_OnMapFail(tempname)
                return False
            shutil.move(settings.OPENRA_PATH + self.legacy_name, tempname)
            name = os.path.splitext(name)[0] + '.oramap'
            self.legacy_map = True

        z = zipfile.ZipFile(tempname, mode='a')
        yamlData = ""
        mapFileContent = []
        for filename in z.namelist():
            mapFileContent.append(filename)
            if filename == "map.yaml":
                mapbytes = z.read(filename)
                yamlData = mapbytes.decode("utf-8")
            if filename.endswith(".lua"):
                self.lua_map = True
        if "map.yaml" not in mapFileContent or "map.bin" not in mapFileContent:
            self.LOG.append('Failed. Invalid map format.')
            misc.send_email_to_admin_OnMapFail(tempname)
            return False
        z.close()

        self.GetHash(tempname)
        userObject = User.objects.get(pk=user_id)
        try:
            hashExists = Maps.objects.get(user_id=userObject.id, map_hash=self.maphash)
            self.LOG.append("Failed. You've already uploaded")
            self.UID = str(hashExists.id)
            return False
        except:
            pass   # all good

        #Load basic map info
        countAdvanced = 0
        shouldCount = False
        expectspawn = False
        for line in string.split(yamlData, '\n'):
            if line[0:5] == "Title":
                self.MapTitle = line[6:].strip().replace("'", "''")
            if line[0:11] == "RequiresMod":
                self.MapMod = line[12:].strip().lower()
            if line[0:6] == "Author":
                self.MapAuthor = line[7:].strip().replace("'", "''")
            if line[0:7] == "Tileset":
                self.MapTileset = line[8:].strip().lower()
            if line[0:4] == "Type":
                self.MapType = line[5:].strip()
            if line[0:11] == "Description":
                self.MapDesc = line[12:].strip().replace("'", "''")
            if line[0:7] == "MapSize":
                self.MapSize = line[8:].strip()
            if line[0:6] == "Bounds":
                self.Bounds = line[7:].strip()
            if line.strip()[-7:] == "mpspawn":
                expectspawn = True
            if line.strip()[0:8] == "Location":
                if expectspawn:
                    self.spawnpoints += line.split(':')[1].strip()+","
                    expectspawn = False
            if line.strip()[0:8] == "Playable":
                state = line.split(':')[1]
                if state.strip().lower() in ['true', 'on', 'yes', 'y']:
                    self.MapPlayers += 1
            if line.strip()[0:13] == "UseAsShellmap":
                state = line.split(':')[1]
                if state.strip().lower() in ['true', 'on', 'yes', 'y']:
                    pass
            if line.strip()[0:5] == "Rules":
                shouldCount = True
            if shouldCount:
                countAdvanced += 1
        self.spawnpoints = self.spawnpoints.rstrip(",")
        if countAdvanced > 20:
            self.advanced_map = True

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

        transac = Maps(
            user = userObject,
            title = self.MapTitle,
            description = self.MapDesc.strip(),
            info = post['info'].strip(),
            author = self.MapAuthor.strip(),
            map_type = self.MapType.strip(),
            players = self.MapPlayers,
            game_mod = self.MapMod,
            map_hash = self.maphash.strip(),
            width = self.MapSize.split(',')[0],
            height = self.MapSize.split(',')[1],
            bounds = self.Bounds,
            spawnpoints = self.spawnpoints,
            tileset = self.MapTileset,
            legacy_map = self.legacy_map,
            revision = rev,
            pre_rev = pre_r,
            next_rev = 0,
            downloading = True,
            requires_upgrade = not self.LintPassed,
            advanced_map = self.advanced_map,
            lua = self.lua_map,
            posted = timezone.now(),
            viewed = 0,
            policy_cc = cc,
            policy_commercial = commercial,
            policy_adaptations = adaptations,
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
        self.LintCheck(self.MapMod)
        if self.LintPassed:
            Maps.objects.filter(id=transac.id).update(requires_upgrade=False)
        else:
            Maps.objects.filter(id=transac.id).update(requires_upgrade=True)

        self.GenerateMinimap()
        #self.GenerateFullPreview(userObject)
        p = multiprocessing.Process(target=utility.PushMapsToRsyncDirs, args=(), name='utility')
        p.start()

        shp = multiprocessing.Process(target=self.GenerateSHPpreview, args=(), name='shppreview')
        shp.start()

    def UnzipMap(self):
        z = zipfile.ZipFile(self.map_full_path_filename, mode='a')
        z.extractall(self.map_full_path_directory + 'content/')
        z.close()

    def GetHash(self, filepath=""):
        if filepath == "":
            filepath = self.map_full_path_filename

        os.chdir(settings.OPENRA_PATH)

        command = 'mono --debug OpenRA.Utility.exe ra --map-hash ' + filepath
        proc = Popen(command.split(), stdout=PIPE).communicate()
        self.maphash = proc[0].strip()
        self.LOG.append(self.maphash)

        os.chdir(self.currentDirectory)

    def LintCheck(self, mod):
        os.chdir(settings.OPENRA_PATH)

        command = 'mono --debug OpenRA.Lint.exe ' + mod + ' ' + self.map_full_path_filename
        proc = Popen(command.split(), stdout=PIPE).communicate()
        if proc[0].strip() == "":
            self.flushLog( ['Yaml check succeeded.'] )
            self.LintPassed = True
        else:
            self.flushLog(proc, "lint")
            self.flushLog( ['Yaml check failed.'] )

        os.chdir(self.currentDirectory)

    def GenerateMinimap(self):
        os.chdir(settings.OPENRA_PATH)

        command = 'mono --debug OpenRA.Utility.exe %s --map-preview %s' % (self.MapMod, self.map_full_path_filename)
        proc = Popen(command.split(), stdout=PIPE).communicate()

        try:
            shutil.move(misc.addSlash(settings.OPENRA_PATH) + self.preview_filename,
                self.map_full_path_directory + os.path.splitext(self.preview_filename)[0] + "-mini.png")
            self.flushLog(proc)
            self.minimap_generated = True
        except:
            self.flushLog( ["Failed to generate minimap for this file."] )        

        os.chdir(self.currentDirectory)

    def GenerateFullPreview(self, userObject):
        os.chdir(settings.OPENRA_PATH)

        command = 'mono --debug OpenRA.Utility.exe %s--full-preview %s' % (self.MapMod, self.map_full_path_filename)
        proc = Popen(command.split(), stdout=PIPE).communicate()

        try:
            shutil.move(misc.addSlash(settings.OPENRA_PATH) + self.preview_filename,
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

    def GenerateSHPpreview(self):
        Dir = os.listdir(self.map_full_path_directory+'content/')
        for fn in Dir:
            if fn.endswith('.shp'):
                os.mkdir(self.map_full_path_directory+'content/png/')
                os.chdir(self.map_full_path_directory+'content/png/')
                command = 'mono --debug %sOpenRA.Utility.exe %s --png %s %s' % (settings.OPENRA_PATH, self.MapMod, self.map_full_path_directory+'content/'+fn, '../../../../palettes/0/RA1/temperat.pal')
                proc = Popen(command.split(), stdout=PIPE).communicate()
                self.flushLog(proc)
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

    def LegacyImport(self, mapPath):
        os.chdir(settings.OPENRA_PATH)
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
