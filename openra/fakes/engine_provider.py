from fs.tempfs import TempFS
from result import Ok

from openra.classes.file_location import FileLocation


class FakeEngineProvider:

    engine_exists:bool
    imported:list

    def __init__(self):
        self.imported = []
        self.engine_exists = False

    def get_path(self, mod:str, version:str):
        if not self.engine_exists:
            return Ok(None)

        temp_fs = TempFS()
        file = 'sample'
        temp_fs.touch(file)
        return Ok(FileLocation(
            TempFS(),
            '',
            file
        ))


    def import_appimage(self, mod:str, version:str, appimage_location:FileLocation):
        self.imported.append({
            'mod': mod,
            'version': version
        })

        temp_fs = TempFS()
        file = 'sample'
        temp_fs.touch(file)
        return Ok(FileLocation(
            TempFS(),
            '',
            file
        ))
