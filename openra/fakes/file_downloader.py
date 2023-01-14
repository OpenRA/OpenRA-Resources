from fs.tempfs import TempFS

from openra.classes.file_location import FileLocation


class FakeFileDownloader:

    def download_file(self, url:str, filename:str):
        temp_fs = TempFS()
        temp_fs.touch(filename)
        return FileLocation(
            temp_fs,
            '',
            filename
        )
