from dependency_injector.wiring import Provide, inject
from django.conf import os
from fs.base import FS
from openra.classes.exceptions import ExceptionBase
from openra.classes.file_location import FileLocation
from openra.classes.release import Release
from openra.services.docker import Docker


class EngineFileRepository:

    _data_fs: FS
    _docker: Docker

    @inject
    def __init__(
        self,
        data_fs: FS = Provide['data_fs'],
        docker: Docker = Provide['docker'],
    ):
        self._data_fs = data_fs
        self._docker = docker

    def exists(self, release: Release):
        path = self._get_target_path(release)

        return self._data_fs.exists(os.path.join(path, 'AppRun'))

    def get_path(self, release: Release):
        path = self._get_target_path_and_throw_exception_if_doesnt_exist(release)

        if not self._data_fs.exists(os.path.join(path, 'AppRun')):
            raise ExceptionEngineAppRunNotFound(self._data_fs, release, path)

        return FileLocation(
            self._data_fs,
            os.path.join('engines', release.mod, release.version),
            ''
        )

    def import_appimage(self, release: Release, appimage_location: FileLocation):
        path = self._get_target_path(release)

        if not self._data_fs.exists(path):
            self._data_fs.makedirs(path)

        # Prevent issues with docker volume naming by copying to tmp
        # appimage_temp needs to be defined in this scope to prevent it getting destroyed too early
        appimage_temp = appimage_location.copy_to_tempfs('appImage')

        self._docker.extract_appimage(
            appimage_temp.get_os_path(),
            self._data_fs.getospath(
                path
            ).decode('utf-8')
        )

        return self.get_path(release)

    def _get_target_path_and_throw_exception_if_doesnt_exist(self, release: Release):
        path = self._get_target_path(release)

        if not self._data_fs.exists(path):
            raise ExceptionEngineFolderNotFound(self._data_fs, release, path)

        return path

    def _get_target_path(self, release):
        return str(os.path.join('engines', release.mod, release.version))


class ExceptionEngineFolderNotFound(ExceptionBase):
    def __init__(self, fs: FS, release: Release, path: str):
        super().__init__()
        self.message = "Folder not found for engine"
        self.detail.append('fs type: ' + str(type(fs)))
        self.detail.append('release: ' + str(release))
        self.detail.append('path: ' + path)


class ExceptionEngineAppRunNotFound(ExceptionBase):
    def __init__(self, fs: FS, release: Release, path: str):
        super().__init__()
        self.message = "AppRun file not found for engine"
        self.detail.append('fs type: ' + str(type(fs)))
        self.detail.append('release: ' + str(release))
        self.detail.append('path: ' + path)
