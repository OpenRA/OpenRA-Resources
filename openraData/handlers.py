import shutil
import os
from subprocess import Popen, PIPE
from django.conf import settings

class MapHandlers():
    
    def __init__(self):
        self.map_is_uploaded = False
        self.minimap_generated = False
        self.maphash = ""
        self.LintPassed = False
        self.map_full_path_directory = ""
        self.map_full_path_filename = ""
        self.minimap_filename = ""
        self.currentDirectory = os.getcwd() + os.sep    # web root
        self.UID = 0
        self.LOG = []

    def ProcessUploading(self, f):
        name = f.name
        badChars = ": ; < > @ $ # & ( ) % '".split()
        for badchar in badChars:
            name = name.replace(badchar, "_")
        name = name.replace(" ", "_")

        self.UID = '1236'
        self.map_full_path_directory = self.currentDirectory + __name__.split('.')[0] + '/data/maps/' + self.UID + '/'
        if not os.path.exists(self.map_full_path_directory):
            os.makedirs(self.map_full_path_directory + 'content')
        self.map_full_path_filename = self.map_full_path_directory + name
        self.minimap_filename = os.path.splitext(name)[0] + ".png"

        with open(self.map_full_path_filename, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)
        self.map_is_uploaded = True
        self.flushLog( ['Map was successfully uploaded as "%s"\n' % name] )
        
        self.UnzipMap()
        self.GetHash()
        self.LintCheck()
        self.GenerateMinimap()

    def UnzipMap(self):
        pass

    def GetHash(self):
        os.chdir(settings.OPENRA_PATH)

        command = 'mono OpenRA.Utility.exe --map-hash ' + self.map_full_path_filename
        proc = Popen(command.split(), stdout=PIPE).communicate()
        self.maphash = proc[0].strip()
        self.flushLog(proc)

        os.chdir(self.currentDirectory)

    def LintCheck(self):
        self.LintPassed = True

    def GenerateMinimap(self):
        os.chdir(settings.OPENRA_PATH)

        command = 'mono OpenRA.Utility.exe --map-preview ' + self.map_full_path_filename
        proc = Popen(command.split(), stdout=PIPE).communicate()
        self.flushLog(proc)

        shutil.move(settings.OPENRA_PATH + self.minimap_filename,
                self.map_full_path_directory + 'content/' + self.minimap_filename)        
        if proc[1] == None: # no output in stderr
            self.minimap_generated = True

        os.chdir(self.currentDirectory)

    def flushLog(self, output=[]):
        logfile = open(self.map_full_path_directory + "log", "a")
        for line in output:
            if line != None:
                logfile.write(line)
                self.LOG.append(line)
        logfile.close()
        return True