from platform import mac_ver
from unittest import TestCase
from unittest.mock import MagicMock, Mock, patch
from fs.memoryfs import MemoryFS
import urllib.request

from fs.tempfs import TempFS
from openra.services.docker import Docker
from openra.services.github import Github

from openra.services.engine_provider import EngineProvider
from openra.structs import FileLocation

class TestServiceEngineProvider(TestCase):

    def test_it_can_return_an_engine_path(self):
        fs = TempFS()
        fs.makedirs('engines/ra/release123')
        fs.touch('engines/ra/release123/AppRun')

        engine_provider = EngineProvider(
            data_fs=fs,
        )

        location = engine_provider.get_path('ra', 'release123')

        self.assertIsInstance(
            location,
            FileLocation
        )

        self.assertEquals(
            location.fs,
            fs
        )

        self.assertEquals(
            location.path,
            'engines/ra/release123',
        )

    def test_it_will_return_none_if_there_are_no_engine_files(self):
        fs = TempFS()

        engine_provider = EngineProvider(
            data_fs=fs
        )

        location = engine_provider.get_path('ra', 'release123')

        self.assertIsNone(
            location
        )

    def test_it_can_import_an_appimage_file(self):
        docker_mock = Mock(spec=Docker)
        docker_mock.extract_appimage = MagicMock(
            return_value = 'sample_output'
        )

        fs=TempFS()
        fs.makedirs('engines/ra/version1')
        fs.touch('engines/ra/version1/AppRun')

        engine_provider = EngineProvider(
            data_fs=fs,
            docker=docker_mock
        )

        appimage_file = FileLocation(
            MemoryFS(),
            '',
            'file'
        )
        appimage_file.fs.touch('file')

        temp_fs_location = appimage_file.copy_to_tempfs('appImageName')

        appimage_file.copy_to_tempfs = MagicMock(
            return_value=temp_fs_location
        )

        location = engine_provider.import_appimage(
            'ra',
            'version1',
            appimage_file
        )

        docker_mock.extract_appimage.assert_called_once_with(
            temp_fs_location.get_os_path(),
            fs.getospath('engines/ra/version1')
        )

        self.assertIsInstance(
            location,
            FileLocation
        )

        self.assertEquals(
            location.fs,
            fs
        )

        self.assertEquals(
            location.path,
            'engines/ra/version1',
        )

    def test_import_appimage_will_return_none_if_docker_returns_none(self):
        docker_mock = Mock(spec=Docker)
        docker_mock.extract_appimage = MagicMock(
            return_value = None
        )

        fs=TempFS()

        engine_provider = EngineProvider(
            data_fs=fs,
            docker=docker_mock
        )

        appimage_file = FileLocation(
            MemoryFS(),
            '',
            'file'
        )
        appimage_file.fs.touch('file')

        temp_fs_location = appimage_file.copy_to_tempfs('appImageName')

        appimage_file.copy_to_tempfs = MagicMock(
            return_value=temp_fs_location
        )

        location = engine_provider.import_appimage(
            'ra',
            'version1',
            appimage_file
        )

        docker_mock.extract_appimage.assert_called_once_with(
            temp_fs_location.get_os_path(),
            fs.getospath('engines/ra/version1')
        )

        self.assertIsNone(
            location,
        )

    def test_import_appimage_will_return_none_if_get_path_returns_none(self):
        docker_mock = Mock(spec=Docker)
        docker_mock.extract_appimage = MagicMock(
            return_value = 'sample_output'
        )

        fs=TempFS()

        engine_provider = EngineProvider(
            data_fs=fs,
            docker=docker_mock
        )

        appimage_file = FileLocation(
            MemoryFS(),
            '',
            'file'
        )
        appimage_file.fs.touch('file')

        temp_fs_location = appimage_file.copy_to_tempfs('appImageName')

        appimage_file.copy_to_tempfs = MagicMock(
            return_value=temp_fs_location
        )

        location = engine_provider.import_appimage(
            'ra',
            'version1',
            appimage_file
        )

        docker_mock.extract_appimage.assert_called_once_with(
            temp_fs_location.get_os_path(),
            fs.getospath('engines/ra/version1')
        )

        self.assertIsNone(
            location,
        )

    def test_an_appimage_can_be_downloaded_before_importing(self):
        temp_fs = TempFS()
        temp_fs.writetext('test', 'sample_content')

        docker_mock = Mock(spec=Docker)
        docker_mock.extract_appimage = MagicMock(
            return_value = 'sample_output'
        )

        data_fs=TempFS()
        data_fs.makedirs('engines/ra/version2')
        data_fs.touch('engines/ra/version2/AppRun')

        engine_provider = EngineProvider(
            data_fs=data_fs,
            docker=docker_mock
        )

        engine_provider._download_appimage = MagicMock(
            return_value=temp_fs.openbin('test')
        )

        location = engine_provider.import_appimage_by_url(
            'ra', 'version2', 'sample_url'
        )

        engine_provider._download_appimage.assert_called_once_with(
            'sample_url'
        )

        self.assertIsInstance(
            location,
            FileLocation
        )

        self.assertEquals(
            location.fs,
            data_fs
        )

        self.assertEquals(
            location.path,
            'engines/ra/version2',
        )

