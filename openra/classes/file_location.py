from django.conf import os
from fs.base import FS, copy
from fs.tempfs import TempFS

from openra.classes.exceptions import ExceptionBase


class FileLocation:

    fs: FS
    path: str
    file: str

    def __init__(self, fs: FS, path: str, file: str):
        self.fs = fs
        self.path = path
        self.file = file

    def get_fs_path(self):
        return os.path.join(self.path + self.file)

    def get_os_dir(self):
        try:
            return self.fs.getospath(
                self.path
            ).decode('utf-8')

        except Exception as exception:
            raise ExceptionFileLocationGetOSDir(exception, self.fs, self.path, self.file)

    def get_os_path(self):
        try:
            return self.fs.getospath(
                self.get_fs_path()
            ).decode('utf-8')

        except Exception as exception:
            raise ExceptionFileLocationGetOSPath(exception, self.fs, self.path, self.file)

    def copy_to_tempfs(self, filename: str):
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

            return FileLocation(
                temp_fs,
                '',
                filename
            )
        except Exception as exception:
            raise ExceptionFileLocationCopyToTempFS(exception, self.fs, self.path, self.file, filename)


class ExceptionFileLocationGetOSDir(ExceptionBase):
    def __init__(self, exception, fs: FS, path: str, file: str):
        super().__init__()
        self.message = "An exception occured while trying to get the os dir"
        self.detail.append('fs type: ' + str(type(fs)))
        self.detail.append('path: ' + path)
        self.detail.append('file: ' + file)
        self.detail.append('message: ' + str(exception))


class ExceptionFileLocationGetOSPath(ExceptionFileLocationGetOSDir):
    def __init__(self, exception, fs: FS, path: str, file: str):
        super().__init__(exception, fs, path, file)
        self.message = "An exception occured while trying to get the os path"


class ExceptionFileLocationCopyToTempFS(ExceptionBase):
    def __init__(self, exception, fs: FS, path: str, file: str, target: str):
        super().__init__()
        self.message = "An exception occured while trying to copy a file to a TempFS"
        self.detail.append('fs type: ' + str(type(fs)))
        self.detail.append('path: ' + path)
        self.detail.append('file: ' + file)
        self.detail.append('target: ' + target)
        self.detail.append('message: ' + str(exception))
