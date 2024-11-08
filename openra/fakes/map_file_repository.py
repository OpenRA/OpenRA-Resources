from fs.tempfs import TempFS

from openra.classes.file_location import FileLocation
from openra.services.map_file_repository import ExceptionMapFolderNotFound


class FakeMapFileRepository:

    map_exists: bool
    lua_paths: list

    def __init__(self):
        self.map_exists = True
        self.lua_paths = []

    def get_oramap_path(self, map_id: int):
        if not self.map_exists:
            raise ExceptionMapFolderNotFound(TempFS(), map_id, 'fake')

        temp_fs = TempFS()
        file = 'sample.oramap'
        temp_fs.touch(file)
        return FileLocation(
            temp_fs,
            '',
            file
        )

    def get_lua_paths(self, map_id: int):
        return self.lua_paths
