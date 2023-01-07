from django.conf import os
from fs.base import FS, copy
from fs.tempfs import TempFS
from result import Err, Ok

from openra.classes.errors import ErrorBase

class FileLocation:

    fs: FS
    path: str
    file: str

    def __init__(self, fs:FS, path:str, file:str):
        self.fs = fs
        self.path = path
        self.file = file

    def get_fs_path(self):
        return os.path.join(self.path + self.file)

    def get_os_dir(self):
        try:
            return Ok(self.fs.getospath(
                self.path
            ).decode('utf-8'))
        except Exception as exception:
            return Err(ErrorFileLocationGetOSDir(exception, self.fs, self.path, self.file))

    def get_os_path(self):
        try:
            return Ok(self.fs.getospath(
                self.get_fs_path()
            ).decode('utf-8'))
        except Exception as exception:
            return Err(ErrorFileLocationGetOSPath(exception, self.fs, self.path, self.file))

    def copy_to_tempfs(self, filename:str):
        try:
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

            return Ok(FileLocation(
                temp_fs,
                '',
                filename
            ))
        except Exception as exception:
            return Err(ErrorFileLocationCopyToTempFS(exception, self.fs, self.path, self.file, filename))

class ErrorFileLocationGetOSDir(ErrorBase):
    def __init__(self, exception, fs:FS, path:str, file:str):
        super().__init__()
        self.message = "An exception occured while trying to get the os dir"
        self.detail.append('fs type: ' + str(type(fs)))
        self.detail.append('path: ' + path)
        self.detail.append('file: ' + file)
        self.detail.append('message: ' + str(exception))

class ErrorFileLocationGetOSPath(ErrorFileLocationGetOSDir):
    def __init__(self, exception, fs:FS, path:str, file:str):
        super().__init__(exception, fs, path, file)
        self.message = "An exception occured while trying to get the os path"

class ErrorFileLocationCopyToTempFS(ErrorBase):
    def __init__(self, exception, fs:FS, path:str, file:str, target:str):
        super().__init__()
        self.message = "An exception occured while trying to copy a file to a TempFS"
        self.detail.append('fs type: ' + str(type(fs)))
        self.detail.append('path: ' + path)
        self.detail.append('file: ' + file)
        self.detail.append('target: ' + target)
        self.detail.append('message: ' + str(exception))
