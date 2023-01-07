

from django.conf import os
from fs.base import FS, copy
from fs.tempfs import TempFS


class FileLocation:

    fs: FS
    path: str
    file: str

    def __init__(self, fs:FS, path:str, file:str):
        self.fs = fs
        self.path = path
        self.file = file

    def get_os_dir(self):
        return self.fs.getospath(
            self.path
        ).decode('utf-8')

    def get_os_path(self):
        return self.fs.getospath(
            self.path + self.file
        ).decode('utf-8')

    def copy_to_tempfs(self, filename):
        temp_fs = TempFS()
        copy.copy_file(
            self.fs,
            os.path.join(
                self.path,
                self.file
            ),
            temp_fs,
            filename
        )
        print('ei')

        loc =FileLocation(
            temp_fs,
            '',
            filename
        )
        path = loc.get_os_path()
        print(path)
        print(os.path.exists(path))

        return loc

