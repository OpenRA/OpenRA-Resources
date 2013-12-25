import shutil

global map_is_uploaded
map
class MapHandlers():
    
    def __init__(self):
        self.map_is_uploaded = False

    def ProcessUploading(self, f):
        with open('/tmp/tempmapfile', 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)
        shutil.move('/tmp/tempmapfile', __name__.split('.')[0] + '/data/mapfile.oramap')
        self.map_is_uploaded = True
