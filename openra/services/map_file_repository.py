from dependency_injector.wiring import Provide, inject
from django.conf import os
from fs.base import FS
from openra.classes.exceptions import ExceptionBase
from openra.classes.file_location import FileLocation


class MapFileRepository:

    _data_fs: FS

    @inject
    def __init__(
        self,
        data_fs: FS = Provide['data_fs']
    ):
        self._data_fs = data_fs

    def get_oramap_path(self, map_id: int):
        path = self._get_target_path_and_throw_exception_if_doesnt_exist(map_id)

        for file in self._data_fs.filterdir(path, ['*.oramap'], None, ['*']):
            return FileLocation(
                self._data_fs,
                path,
                file.name
            )

        raise ExceptionOramapNotFound(self._data_fs, map_id, path)

    def _get_target_path_and_throw_exception_if_doesnt_exist(self, map_id: int):
        path = self._get_target_path(map_id)

        if not self._data_fs.exists(path):
            raise ExceptionMapFolderNotFound(self._data_fs, map_id, path)

        return path

    def _get_target_path(self, map_id: int):
        return os.path.join('maps', str(map_id))


class ExceptionMapFolderNotFound(ExceptionBase):
    def __init__(self, fs: FS, map_id: int, path: str):
        super().__init__()
        self.message = "Folder not found for map"
        self.detail.append('fs type: ' + str(type(fs)))
        self.detail.append('map: ' + str(map_id))
        self.detail.append('path: ' + path)


class ExceptionOramapNotFound(ExceptionBase):
    def __init__(self, fs: FS, map_id: int, path: str):
        super().__init__()
        self.message = "Oramap file not found for map"
        self.detail.append('fs type: ' + str(type(fs)))
        self.detail.append('map: ' + str(map_id))
        self.detail.append('path: ' + path)
