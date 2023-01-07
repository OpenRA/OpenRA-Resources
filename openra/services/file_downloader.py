import urllib3
from fs.tempfs import TempFS
from result import Err, Ok

from openra.classes.errors import ErrorBase
from openra.classes.file_location import FileLocation


class FileDownloader:

    def download_file(self, url:str, filename:str):
        try:
            temp_fs = self._create_temp_fs()

            file_like_request = self._get_file_like_object(url)
            if isinstance(file_like_request, Err):
                return file_like_request

            temp_fs.writefile(filename, file_like_request.unwrap())

            return Ok(FileLocation(
                temp_fs,
                '',
                filename
            ))
        except Exception as exception:
            return Err(ErrorFileDownloaderStoreFile(exception, url))

    def _create_temp_fs(self):
        return TempFS()

    def _get_file_like_object(self, url):
        try:
            http = urllib3.PoolManager()
            return Ok(http.request('GET', url, preload_content=False))
        except Exception as exception:
            return Err(ErrorFileDownloaderRetrieveFile(exception, url))

class ErrorFileDownloaderRetrieveFile(ErrorBase):
    def __init__(self, exception, url:str):
        super().__init__()
        self.message = "File downloader caught an exception while attempting to retrieve this file"
        self.detail.append('url: ' + url)
        self.detail.append('message: ' + str(exception))

class ErrorFileDownloaderStoreFile(ErrorBase):
    def __init__(self, exception, url:str):
        super().__init__()
        self.message = "File downloader caught an exception while attempting to store this file"
        self.detail.append('url: ' + url)
        self.detail.append('message: ' + str(exception))
