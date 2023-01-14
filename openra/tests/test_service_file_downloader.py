from unittest import TestCase
from unittest.mock import MagicMock

from fs.tempfs import TempFS

from openra.services.file_downloader import ExceptionFileDownloader, FileDownloader

class TestServiceFileDownloader(TestCase):

    def create_mock_file_like_object(self, content:str):
        temp_fs = TempFS()
        temp_fs.writetext('test', content)
        return temp_fs.openbin('test')


    def test_download_file_downloads_a_file(self):
        file_downloader = FileDownloader()

        file_downloader._get_file_like_object = MagicMock(
            return_value = self.create_mock_file_like_object('sample')
        )

        location = file_downloader.download_file('test_url', 'file_name')

        self.assertEquals(
            'sample',
            location.fs.readtext(
                location.get_fs_path()
            )
        )

    def test_download_file_throws_exception_when_lib_throws_exception(self):
        file_downloader = FileDownloader()

        file_downloader._get_file_like_object = MagicMock(
            side_effect = Exception()
        )

        self.assertRaises(
            ExceptionFileDownloader,
            file_downloader.download_file,
            'test_url',
            'file_name'
        )
