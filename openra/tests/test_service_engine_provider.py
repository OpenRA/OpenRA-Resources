from unittest import TestCase
from unittest.mock import MagicMock, Mock
from fs.memoryfs import MemoryFS

from fs.tempfs import TempFS
from result import Err, Ok
from openra.classes.errors import ErrorBase
from openra.classes.file_location import FileLocation
from openra.services.docker import Docker

from openra.services.engine_provider import EngineProvider, ErrorEngineProviderGetPath

class TestServiceEngineProvider(TestCase):

    def test_it_can_return_an_engine_path(self):
        fs = TempFS()
        fs.makedirs('engines/ra/release123')
        fs.touch('engines/ra/release123/AppRun')

        engine_provider = EngineProvider(
            data_fs=fs,
        )

        location = engine_provider.get_path('ra', 'release123').unwrap()

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

        location = engine_provider.get_path('ra', 'release123').unwrap()

        self.assertIsNone(
            location
        )

    def test_it_will_return_an_error_if_an_exception_is_caught(self):
        fs = Mock(spec=TempFS)

        fs.exists = MagicMock(
            side_effect = Exception()
        )

        engine_provider = EngineProvider(
            data_fs=fs
        )

        result = engine_provider.get_path('ra', 'release123').unwrap_err()

        self.assertIsInstance(
            result,
            ErrorEngineProviderGetPath
        )

    def test_it_can_import_an_appimage_file(self):
        docker_mock = Mock(spec=Docker)
        docker_mock.extract_appimage = MagicMock(
            return_value = Ok('sample_output')
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

        temp_fs_location = appimage_file.copy_to_tempfs('appImageName').unwrap()

        appimage_file.copy_to_tempfs = MagicMock(
            return_value=Ok(temp_fs_location)
        )

        location = engine_provider.import_appimage(
            'ra',
            'version1',
            appimage_file
        ).unwrap()

        docker_mock.extract_appimage.assert_called_once_with(
            temp_fs_location.get_os_path().unwrap(),
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

    def test_import_appimage_will_return_an_error_if_docker_returns_an_error(self):
        docker_mock = Mock(spec=Docker)
        docker_mock.extract_appimage = MagicMock(
            return_value = Err(ErrorBase())
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

        temp_fs_location = appimage_file.copy_to_tempfs('appImageName').unwrap()

        appimage_file.copy_to_tempfs = MagicMock(
            return_value=Ok(temp_fs_location)
        )

        result = engine_provider.import_appimage(
            'ra',
            'version1',
            appimage_file
        )

        docker_mock.extract_appimage.assert_called_once_with(
            temp_fs_location.get_os_path().unwrap(),
            fs.getospath('engines/ra/version1').decode('utf-8')
        )

        self.assertIsInstance(
            result.unwrap_err(),
            ErrorBase
        )

    def test_import_appimage_will_return_none_if_get_path_returns_none(self):
        docker_mock = Mock(spec=Docker)
        docker_mock.extract_appimage = MagicMock(
            return_value = Ok('sample_output')
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

        temp_fs_location = appimage_file.copy_to_tempfs('appImageName').unwrap()

        appimage_file.copy_to_tempfs = MagicMock(
            return_value=Ok(temp_fs_location)
        )

        location = engine_provider.import_appimage(
            'ra',
            'version1',
            appimage_file
        )

        docker_mock.extract_appimage.assert_called_once_with(
            temp_fs_location.get_os_path().unwrap(),
            fs.getospath('engines/ra/version1').decode('utf-8')
        )

        self.assertIsNone(
            location.unwrap(),
        )

