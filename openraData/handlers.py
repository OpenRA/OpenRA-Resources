import shutil

def handle_uploaded_map(f):
    with open('/tmp/tempmapfile', 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    shutil.move('/tmp/tempmapfile', __name__.split('.')[0] + '/data/mapfile.oramap')
