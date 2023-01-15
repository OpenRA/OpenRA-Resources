from unittest import TestCase
from unittest.mock import MagicMock, Mock
from fs.memoryfs import MemoryFS

from fs.tempfs import TempFS
from openra.classes.file_location import FileLocation
from openra.services.map_file_repository import ExceptionMapFolderNotFound, ExceptionOramapNotFound, MapFileRepository

class TestServiceMapFileRepository(TestCase):

    def test_get_oramap_path_returns_map_oramap_path(self):
        fs = TempFS()
        fs.makedirs('maps/1')
        fs.touch('maps/1/mymap.oramap')

        map_file_repository = MapFileRepository(
            data_fs=fs,
        )

        location = map_file_repository.get_oramap_path(1)

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
            'maps/1',
        )

        self.assertEquals(
            location.file,
            'mymap.oramap',
        )

    def test_get_oramap_path_throws_exception_if_folder_doesnt_exist(self):
        fs = TempFS()

        map_file_repository = MapFileRepository(
            data_fs=fs,
        )

        self.assertRaises(
            ExceptionMapFolderNotFound,
            map_file_repository.get_oramap_path,
            1
        )

    def test_get_oramap_path_throws_exception_if_no_oramap_exists(self):
        fs = TempFS()
        fs.makedirs('maps/1/content')
        fs.touch('maps/1/mymap.notoramap')

        map_file_repository = MapFileRepository(
            data_fs=fs,
        )

        self.assertRaises(
            ExceptionOramapNotFound,
            map_file_repository.get_oramap_path,
            1
        )
