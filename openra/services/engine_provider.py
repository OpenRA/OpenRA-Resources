import urllib.request

from dependency_injector.wiring import Provide, inject
from django.conf import os
from fs.base import FS
from fs.tempfs import TempFS
from result import Err, Ok
from openra.classes.errors import ErrorBase
from openra.classes.file_location import FileLocation
from openra.services.docker import Docker
from openra.services.github import Github
import urllib3

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
                return Ok(None)

            return Ok(FileLocation(
                self._data_fs,
                os.path.join('engines', mod, version),
                ''
            ))
        except Exception as exception:
            return Err(ErrorEngineProviderGetPath(exception, self._data_fs, mod, version))


    def import_appimage(self, mod:str, version:str, appimage_location:FileLocation):
        path = self._get_target_path(mod, version)

        if not self._data_fs.exists(path):
            self._data_fs.makedirs(path)

        # Prevent issues with docker volume n naming by copying to tmp
        appimage_temp_result = appimage_location.copy_to_tempfs('appImage')
        if isinstance(appimage_temp_result, Err):
            return appimage_temp_result

        appimage_temp = appimage_temp_result.unwrap()

        appimage_os_path_result = appimage_temp.get_os_path()
        if isinstance(appimage_os_path_result, Err):
            return appimage_os_path_result

        extract_appimage_result = self._docker.extract_appimage(
            appimage_os_path_result.unwrap(),
            self._data_fs.getospath(
                path
            ).decode('utf-8')
        )
        if isinstance(extract_appimage_result, Err):
            return extract_appimage_result

        return self.get_path(mod, version)

    def _get_target_path(self, mod, version):
        return str(os.path.join('engines', mod, version))

class ErrorEngineProviderGetPath(ErrorBase):
    def __init__(self, exception, fs:FS, mod:str, version:str):
        super().__init__()
        self.message = "Engine provider caught an exception while looking up an engine path"
        self.detail.append('fs type: ' + str(type(fs)))
        self.detail.append('mod: ' + mod)
        self.detail.append('version: ' + version)
        self.detail.append('message: ' + str(exception))
