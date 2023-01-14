from dependency_injector.wiring import Provide, inject
from django.conf import os
from fs.base import FS
from openra.classes.exceptions import ExceptionBase
from openra.classes.file_location import FileLocation
from openra.services.docker import Docker

class EngineProvider:

    _data_fs: FS
    _docker: Docker

    @inject
    def __init__(
            self,
            data_fs:FS=Provide['data_fs'],
            docker:Docker=Provide['docker'],
        ):
        self._data_fs = data_fs
        self._docker = docker

    def get_path(self, mod:str, version:str):
        try:
            path = self._get_target_path(mod, version)

            if not self._data_fs.exists(os.path.join(path, 'AppRun')):
                return None

            return FileLocation(
                self._data_fs,
                os.path.join('engines', mod, version),
                ''
            )
        except Exception as exception:
            raise ExceptionEngineProviderGetPath(exception, self._data_fs, mod, version)


    def import_appimage(self, mod:str, version:str, appimage_location:FileLocation):
        path = self._get_target_path(mod, version)

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

        return self.get_path(mod, version)

    def _get_target_path(self, mod, version):
        return str(os.path.join('engines', mod, version))

class ExceptionEngineProviderGetPath(ExceptionBase):
    def __init__(self, exception, fs:FS, mod:str, version:str):
        super().__init__()
        self.message = "Engine provider caught an exception while looking up an engine path"
        self.detail.append('fs type: ' + str(type(fs)))
        self.detail.append('mod: ' + mod)
        self.detail.append('version: ' + version)
        self.detail.append('message: ' + str(exception))
