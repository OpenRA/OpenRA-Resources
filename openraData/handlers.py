import shutil
import os
from subprocess import Popen, PIPE
from django.conf import settings

class MapHandlers():
    
    def __init__(self):
        self.map_is_uploaded = False
        self.minimap_generated = False

    def ProcessUploading(self, f):
        with open('/tmp/tempMapfile', 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)
        name = f.name
        badChars = ": ; < > @ $ # & ( ) % '".split()
        for badchar in badChars:
            name = name.replace(badchar, "_")
        name = name.replace(" ", "_")

        newDestination = __name__.split('.')[0] + '/data/' + name   # relative path
        shutil.move('/tmp/tempMapfile', newDestination)
        self.map_is_uploaded = True
        
        self.LintCheck(newDestination)
        self.GenerateMinimap(newDestination)

    def LintCheck(self, filepath):
        pass

    def GenerateMinimap(self, filepath):
        current_working_dir = os.getcwd() + os.sep
        full_path_to_map = current_working_dir + filepath
        basename_png = os.path.splitext(os.path.basename(filepath))[0] + ".png"
        map_dir = current_working_dir + os.path.dirname(filepath) + os.sep

        os.chdir(settings.OPENRA_PATH)
        command = 'mono OpenRA.Utility.exe --map-preview ' + full_path_to_map
        proc = Popen(command.split(), stdout=PIPE).communicate()
        logfile = open(map_dir + "log", "a")
        for line in proc:
            if line != None:
                logfile.write(line + "\n")
        logfile.close()
        shutil.move(settings.OPENRA_PATH + basename_png, map_dir + basename_png)
        
        os.chdir(current_working_dir)
        self.minimap_generated = True