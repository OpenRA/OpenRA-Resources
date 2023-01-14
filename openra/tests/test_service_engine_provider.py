from unittest import TestCase
from unittest.mock import MagicMock, Mock
from fs.memoryfs import MemoryFS

from fs.tempfs import TempFS
from openra.classes.exceptions import ExceptionBase
from openra.classes.file_location import FileLocation
from openra.services.docker import Docker

from openra.services.engine_provider import EngineProvider, ExceptionEngineProviderGetPath

class TestServiceEngineProvider(TestCase):

    def test_get_path_returns_engine_path(self):
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

    def test_get_path_returns_none_where_no_engine_files(self):
        fs = TempFS()

        engine_provider = EngineProvider(
            data_fs=fs
        )

        location = engine_provider.get_path('ra', 'release123')

        self.assertIsNone(
            location
        )

    def test_get_path_throws_exception_when_exception_caught(self):
        fs = Mock(spec=TempFS)

        fs.exists = MagicMock(
            side_effect = Exception()
        )

        engine_provider = EngineProvider(
            data_fs=fs
        )


        self.assertRaises(
            ExceptionEngineProviderGetPath,
            engine_provider.get_path,
            'ra',
            'release123'
        )

    def test_import_appimage_imports_appimage(self):
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
            fs.getospath('engines/ra/version1').decode('utf-8')
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
            fs.getospath('engines/ra/version1').decode('utf-8')
        )

        self.assertIsNone(
            location
        )

