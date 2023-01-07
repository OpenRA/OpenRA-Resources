from unittest import TestCase
from unittest.mock import MagicMock

from fs.tempfs import TempFS
from result import Ok

from openra.services.file_downloader import ErrorFileDownloaderStoreFile, FileDownloader

class TestServiceFileDownloader(TestCase):

    def create_mock_file_like_object(self, content:str):
        temp_fs = TempFS()
        temp_fs.writetext('test', content)
        return temp_fs.openbin('test')


    def test_can_download_a_file(self):
        file_downloader = FileDownloader()

        file_downloader._get_file_like_object = MagicMock(
            return_value = Ok(self.create_mock_file_like_object('sample'))
        )

        location = file_downloader.download_file('test_url', 'file_name').unwrap()

        self.assertEquals(
            'sample',
            location.fs.readtext(
                location.get_fs_path()
            )
        )

    def test_will_return_an_err_if_the_downloader_lib_throws_an_exception(self):
        file_downloader = FileDownloader()

        file_downloader._get_file_like_object = MagicMock(
            side_effect = Exception()
        )

        result = file_downloader.download_file('test_url', 'file_name')

        self.assertIsInstance(
            result.unwrap_err(),
            ErrorFileDownloaderStoreFile
        )
