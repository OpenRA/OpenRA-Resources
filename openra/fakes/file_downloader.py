from fs.tempfs import TempFS

from openra.classes.file_location import FileLocation


class FakeFileDownloader:

    downloaded: list

    def __init__(self):
        self.downloaded = []

    def download_file(self, url: str, filename: str):
        self.downloaded.append({
            'url': url,
            'filename': filename
        })

        temp_fs = TempFS()
        temp_fs.touch(filename)
        return FileLocation(
            temp_fs,
            '',
            filename
        )
