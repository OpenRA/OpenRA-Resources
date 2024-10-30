from __future__ import annotations
import io
from django.conf import os
from fs import filesize
from fs.base import FS, copy
from fs.tempfs import TempFS
import re

from openra.classes.exceptions import ExceptionBase


class FileLocation:

    fs: FS
    path: str
    file: str

    def __init__(self, fs: FS, path: str, file: str):
        self.fs = fs
        self.path = path
        self.file = file

    def get_file_basename(self):
        return re.sub(r"\.[^\.]+$", "", self.file)

    def get_file_extension(self):
        search = re.search(r"\.([^\.]+)$", self.file)
        if (search is None):
            return ""

        return search.group(1)

    def get_fs_path(self):
        return os.path.join(self.path, self.file)

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

    def ensure_file_exists(self):
        if not self.fs.exists(self.get_fs_path()):
            if self.path:
                self.fs.makedirs(self.path)
            self.fs.create(self.get_fs_path())

    def get_file_size_formatted(self):
        info = self.fs.getinfo(self.get_fs_path(), ["details"])

        return filesize.traditional(info.size)

    def open(self, mode):
        return self.fs.open(self.get_fs_path(), mode)

    def copy_to_file_location(self, location: FileLocation):
        try:
            location.ensure_file_exists()
            copy.copy_file(
                self.fs,
                os.path.join(
                    self.path,
                    self.file
                ),
                location.fs,
                location.get_fs_path()
            )

            return location

        except Exception as exception:
            raise ExceptionFileLocationCopyToFileLocation(exception, self.fs, self.path, self.file, location)

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

    def get_file_clone(self):
        try:

            file = io.BytesIO()

            self.fs.download(
                self.get_fs_path(),
                file
            )

            file.seek(0)

            return file

        except Exception as exception:
            raise ExceptionFileLocationGetFileClone(exception, self.fs, self.path, self.file)


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


class ExceptionFileLocationCopyToFileLocation(ExceptionBase):
    def __init__(self, exception, fs: FS, path: str, file: str, target: FileLocation):
        super().__init__()
        self.message = "An exception occured while trying to copy a file to a TempFS"
        self.detail.append('from fs type: ' + str(type(fs)))
        self.detail.append('from path: ' + path)
        self.detail.append('from file: ' + file)
        self.detail.append('to fs type: ' + str(type(target.fs)))
        self.detail.append('to path: ' + target.path)
        self.detail.append('to file: ' + target.file)
        self.detail.append('message: ' + str(exception))


class ExceptionFileLocationCopyToTempFS(ExceptionBase):
    def __init__(self, exception, fs: FS, path: str, file: str, target: str):
        super().__init__()
        self.message = "An exception occured while trying to copy a file to a TempFS"
        self.detail.append('fs type: ' + str(type(fs)))
        self.detail.append('path: ' + path)
        self.detail.append('file: ' + file)
        self.detail.append('target: ' + target)
        self.detail.append('message: ' + str(exception))


class ExceptionFileLocationGetFileClone(ExceptionBase):
    def __init__(self, exception, fs: FS, path: str, file: str):
        super().__init__()
        self.message = "An exception occured while trying to clone a file"
        self.detail.append('fs type: ' + str(type(fs)))
        self.detail.append('path: ' + path)
        self.detail.append('file: ' + file)
        self.detail.append('message: ' + str(exception))
