import shutil
import os
import magic
import zipfile
import string
import re
from subprocess import Popen, PIPE
import multiprocessing

from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from openraData.models import Maps
from openraData.models import Units
from openraData.models import Mods
from openraData.models import Screenshots
from openraData import triggers, misc

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

        self.MapMod = ""
        self.MapTitle = ""
        self.MapAuthor = ""
        self.MapTileset = ""
        self.MapType = ""
        self.MapSize = ""
        self.MapDesc = ""
        self.MapPlayers = 0

        self.revisions = []

    def ProcessUploading(self, user_id, f, post, rev=1, pre_r=0):
        tempname = '/tmp/oramaptemp.oramap'
        with open(tempname, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)

        mimetype = magic.from_file(tempname, mime=True)
        if mimetype != 'application/zip' or os.path.splitext(f.name)[1] != '.oramap':
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
            if line.strip()[0:8] == "Playable":
                state = line.split(':')[1]
                if state.strip().lower() in ['true', 'on', 'yes', 'y']:
                    self.MapPlayers += 1
            if line.strip()[0:13] == "UseAsShellmap":
                state = line.split(':')[1]
                if state.strip().lower() in ['true', 'on', 'yes', 'y']:
                    self.LOG.append('Failed. Reason: %s' % line)
                    return False
            if line.strip()[0:5] == "Rules":
                shouldCount = True
            if shouldCount:
                countAdvanced += 1
        if countAdvanced > 20:
            self.advanced_map = True

        cc = False
        commercial = False
        adaptations = ""
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

        transac = Maps(
            user = userObject,
            title = self.MapTitle,
            description = self.MapDesc,
            info = post['info'],
            author = self.MapAuthor,
            map_type = self.MapType,
            players = self.MapPlayers,
            game_mod = self.MapMod,
            map_hash = self.maphash,
            width = self.MapSize.split(',')[0],
            height = self.MapSize.split(',')[1],
            tileset = self.MapTileset,
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

        self.GenerateMinimap()
        #self.GenerateFullPreview(userObject)
        p = multiprocessing.Process(target=triggers.PushMapsToRsyncDirs, args=(), name='triggers')
        p.start()

    def UnzipMap(self):
        z = zipfile.ZipFile(self.map_full_path_filename, mode='a')
        z.extractall(self.map_full_path_directory + 'content/')
        z.close()

    def GetHash(self, filepath=""):
        if filepath == "":
            filepath = self.map_full_path_filename

        os.chdir(settings.OPENRA_PATH)

        command = 'mono OpenRA.Utility.exe --map-hash ' + filepath
        proc = Popen(command.split(), stdout=PIPE).communicate()
        self.maphash = proc[0].strip()
        self.LOG.append(self.maphash)

        os.chdir(self.currentDirectory)

    def LintCheck(self, mod):
        os.chdir(settings.OPENRA_PATH)

        command = 'mono OpenRA.Lint.exe ' + mod + ' ' + self.map_full_path_filename
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

        command = 'mono OpenRA.Utility.exe --map-preview ' + self.map_full_path_filename
        proc = Popen(command.split(), stdout=PIPE).communicate()

        try:
            shutil.move(misc.addShash(settings.OPENRA_PATH) + self.preview_filename,
                self.map_full_path_directory + os.path.splitext(self.preview_filename)[0] + "-mini.png")
            self.flushLog(proc)
            self.minimap_generated = True
        except:
            self.flushLog( ["Failed to generate minimap for this file."] )        

        os.chdir(self.currentDirectory)

    def GenerateFullPreview(self, userObject):
        os.chdir(settings.OPENRA_PATH)

        command = 'mono OpenRA.Utility.exe --full-preview ' + self.map_full_path_filename
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

    def flushLog(self, output=[], lint=""):
        logfile = open(self.map_full_path_directory + lint + "log", "a")
        for line in output:
            if line != None:
                logfile.write(line.strip() + "\n")
                if lint == "":
                    self.LOG.append(line.strip())
        logfile.close()
        return True

########## Revisions

def GetRevisions(self, itemid, modelName, seek_next=False):
    if seek_next:
        if modelName.lower() == "maps":
            itemObject = Maps.objects.get(id=itemid)
        elif modelName.lower() == "units":
            itemObject = Units.objects.get(id=itemid)
        elif modelName.lower() == "mods":
            itemObject = Mods.objects.get(id=itemid)
        if itemObject.next_rev == 0:
            return
        self.revisions.append(itemObject.next_rev)
        self.GetRevisions(itemObject.next_rev, True)
        return
    self.revisions.insert(0, itemid)
    if modelName.lower() == "maps":
        itemObject = Maps.objects.get(id=itemid)
    elif modelName.lower() == "units":
        itemObject = Units.objects.get(id=itemid)
    elif modelName.lower() == "mods":
        itemObject = Mods.objects.get(id=itemid)
    if itemObject.pre_rev == 0:
        self.GetRevisions(self.revisions[-1], modelName, True)
        return
    self.GetRevisions(itemObject.pre_rev)

def GetLatestRevisionID(self, itemid, modelName):
    if modelName.lower() == "maps":
        itemObject = Maps.objects.get(id=itemid)
    elif modelName.lower() == "units":
        itemObject = Units.objects.get(id=itemid)
    elif modelName.lower() == "mods":
        itemObject = Mods.objects.get(id=itemid)
    if itemObject.next_rev == 0:
        return itemObject.id
    return self.GetLatestRevisionID(itemObject.next_rev)

##########

def DeleteMap(self, itemid):
    pass

def DeleteUnit(self, itemid):
    pass

def DeleteMod(self, itemid):
    pass

def DeletePalette(self, itemid):
    pass

def DeleteReplay(self, itemid):
    pass

def DeleteScreenshot(self, itemid):
    pass

def NotifyOnFail(self, message, tempname):
    # send an email to admin attaching file which is already saved in temp location
    pass
