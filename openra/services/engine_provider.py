import urllib.request

from dependency_injector.wiring import Provide, inject
from django.conf import os
from fs.base import FS
from fs.tempfs import TempFS
from openra.services.docker import Docker
from openra.services.github import Github

from openra.structs import FileLocation


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
        path = self._get_target_path(mod, version)

        if not self._data_fs.exists(os.path.join(path, 'AppRun')):
            return None

        return FileLocation(
            self._data_fs,
            os.path.join('engines', mod, version),
            ''
        )

    def import_appimage(self, mod:str, version:str, appimage_location:FileLocation):
        path = self._get_target_path(mod, version)
        if not self._data_fs.exists(path):
            self._data_fs.makedirs(path)
        appimage_temp:FileLocation = appimage_location.copy_to_tempfs('appImage')
        if self._docker.extract_appimage(
            # Prevent issues with docker volume n naming
            appimage_temp.get_os_path(),
            self._data_fs.getospath(
                path
            ).decode('utf-8')
            ) == None:
            return None

        return self.get_path(mod, version)

    def import_appimage_by_url(self, mod, version, appimage_url):
        appimage_location = self._download_appimage_and_create_fs(appimage_url)

        if(appimage_location is None):
            return None

        return self.import_appimage(mod, version, appimage_location)


    def _get_target_path(self, mod, version):
        return str(os.path.join('engines', mod, version))

    def _download_appimage_and_create_fs(self, url):
        temp_fs = TempFS()

        file = self._download_appimage(url)

        temp_fs.writefile('appImage', file)

        return FileLocation(
            temp_fs,
            '',
            'appImage'
        )

    def _download_appimage(self, url):
        # This could probably be passed out to another service as
        # it's an unknown atm
        return urllib.request.urlopen(url)

