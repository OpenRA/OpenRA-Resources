import urllib3
from fs.tempfs import TempFS

from openra.classes.exceptions import ExceptionBase
from openra.classes.file_location import FileLocation

class FileDownloader:

    def download_file(self, url:str, filename:str):
        try:
            temp_fs = self._create_temp_fs()

            temp_fs.writefile(
                filename,
                self._get_file_like_object(url)
            )

            return FileLocation(
                temp_fs,
                '',
                filename
            )
        except Exception as exception:
            raise ExceptionFileDownloader(exception, url)

    def _create_temp_fs(self):
        return TempFS()

    def _get_file_like_object(self, url):
        http = urllib3.PoolManager()
        return http.request('GET', url, preload_content=False)

class ExceptionFileDownloader(ExceptionBase):
    def __init__(self, exception, url:str):
        super().__init__()
        self.message = "File downloader caught an exception while attempting to download this file"
        self.detail.append('url: ' + url)
        self.detail.append('message: ' + str(exception))
