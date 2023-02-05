from unittest import TestCase
from unittest.mock import MagicMock, Mock
from fs.memoryfs import MemoryFS

from fs.tempfs import TempFS
from openra.classes.file_location import FileLocation
from openra.classes.release import Release
from openra.services.docker import Docker

from openra.services.engine_file_repository import EngineFileRepository, ExceptionEngineAppRunNotFound, ExceptionEngineFolderNotFound


class TestServiceEngineFileRepository(TestCase):

    def test_exists_returns_whether_engine_exists(self):
        fs = TempFS()

        engine_file_repository = EngineFileRepository(
            data_fs=fs,
        )

        release = Release('ra', 'release123', False)

        self.assertFalse(
            engine_file_repository.exists(release)
        )

        fs.makedirs('engines/ra/release123')

        self.assertFalse(
            engine_file_repository.exists(release)
        )

        fs.touch('engines/ra/release123/AppRun')

        self.assertTrue(
            engine_file_repository.exists(release)
        )

    def test_get_path_returns_engine_path(self):
        fs = TempFS()
        fs.makedirs('engines/ra/release123')
        fs.touch('engines/ra/release123/AppRun')

        engine_file_repository = EngineFileRepository(
            data_fs=fs,
        )

        release = Release('ra', 'release123', False)

        location = engine_file_repository.get_path(release)

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

    def test_get_path_throws_exception_when_folder_doesnt_exist(self):
        fs = TempFS()

        engine_file_repository = EngineFileRepository(
            data_fs=fs
        )

        self.assertRaises(
            ExceptionEngineFolderNotFound,
            engine_file_repository.get_path,
            Release('ra', 'release123', False)
        )

    def test_get_path_throws_exception_when_apprun_doesnt_exist(self):
        fs = TempFS()
        fs.makedirs('engines/ra/release123')

        engine_file_repository = EngineFileRepository(
            data_fs=fs
        )

        self.assertRaises(
            ExceptionEngineAppRunNotFound,
            engine_file_repository.get_path,
            Release('ra', 'release123', False)
        )

    def test_import_appimage_imports_appimage(self):
        docker_mock = Mock(spec=Docker)
        docker_mock.extract_appimage = MagicMock(
            return_value='sample_output'
        )

        fs = TempFS()
        fs.makedirs('engines/ra/version1')
        fs.touch('engines/ra/version1/AppRun')

        engine_file_repository = EngineFileRepository(
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

        location = engine_file_repository.import_appimage(
            Release('ra', 'version1', False),
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

    def test_import_appimage_throws_exception_if_engine_doesnt_exist_after_import(self):
        docker_mock = Mock(spec=Docker)
        docker_mock.extract_appimage = MagicMock(
            return_value='sample_output'
        )

        fs = TempFS()

        engine_file_repository = EngineFileRepository(
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

        self.assertRaises(
            ExceptionEngineAppRunNotFound,
            engine_file_repository.import_appimage,
            Release('ra', 'version1', False),
            appimage_file
        )

        docker_mock.extract_appimage.assert_called_once_with(
            temp_fs_location.get_os_path(),
            fs.getospath('engines/ra/version1').decode('utf-8')
        )
