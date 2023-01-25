from typing import List
from fs.tempfs import TempFS

from openra.classes.file_location import FileLocation
from openra.classes.release import Release
from openra.services.engine_file_repository import ExceptionEngineFolderNotFound


class FakeEngineFileRepository:

    engine_exists: bool
    imported: List[Release]

    def __init__(self):
        self.imported = []
        self.engine_exists = False

    def exists(self, release: Release):
        return self.engine_exists

    def get_path(self, release: Release):
        if not self.engine_exists:
            raise ExceptionEngineFolderNotFound(TempFS(), release, 'fake')

        temp_fs = TempFS()
        file = 'sample'
        temp_fs.touch(file)
        return FileLocation(
            temp_fs,
            '',
            file
        )

    def import_appimage(self, release: Release, appimage_location: FileLocation):
        self.imported.append(release)

        temp_fs = TempFS()
        file = 'sample'
        temp_fs.touch(file)
        return FileLocation(
            temp_fs,
            '',
            file
        )
