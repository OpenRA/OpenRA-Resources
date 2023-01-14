from fs.tempfs import TempFS

from openra.classes.file_location import FileLocation
from openra.services.engine_file_repository import ExceptionEngineFolderNotFound


class FakeEngineFileRepository:

    engine_exists:bool
    imported:list

    def __init__(self):
        self.imported = []
        self.engine_exists = False

    def exists(self, mod:str, version:str):
        return self.engine_exists

    def get_path(self, mod:str, version:str):
        if not self.engine_exists:
            raise ExceptionEngineFolderNotFound(TempFS(), mod, version, 'fake')

        temp_fs = TempFS()
        file = 'sample'
        temp_fs.touch(file)
        return FileLocation(
            TempFS(),
            '',
            file
        )


    def import_appimage(self, mod:str, version:str, appimage_location:FileLocation):
        self.imported.append({
            'mod': mod,
            'version': version
        })

        temp_fs = TempFS()
        file = 'sample'
        temp_fs.touch(file)
        return FileLocation(
            TempFS(),
            '',
            file
        )
