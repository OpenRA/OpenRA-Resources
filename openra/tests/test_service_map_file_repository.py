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
        fs.makedirs('maps/1')
        fs.touch('maps/1/mymap.notoramap')

        map_file_repository = MapFileRepository(
            data_fs=fs,
        )

        self.assertRaises(
            ExceptionOramapNotFound,
            map_file_repository.get_oramap_path,
            1
        )

    def test_get_lua_paths_returns_map_lua_paths(self):
        fs = TempFS()
        fs.makedirs('maps/1/content')
        fs.touch('maps/1/mymap.oramap')
        fs.touch('maps/1/content/mylua1.lua')
        fs.touch('maps/1/content/mylua2.lua')
        fs.touch('maps/1/content/somefile.yaml')

        map_file_repository = MapFileRepository(
            data_fs=fs,
        )

        locations = map_file_repository.get_lua_paths(1)

        self.assertEquals(2, len(locations))

        self.assertIsInstance(
            locations[0],
            FileLocation
        )

        self.assertEquals(
            locations[0].fs,
            fs
        )

        self.assertEquals(
            locations[0].path,
            'maps/1/content',
        )

        self.assertEquals(
            locations[0].file,
            'mylua1.lua',
        )

        self.assertIsInstance(
            locations[1],
            FileLocation
        )

        self.assertEquals(
            locations[1].fs,
            fs
        )

        self.assertEquals(
            locations[1].path,
            'maps/1/content',
        )

        self.assertEquals(
            locations[1].file,
            'mylua2.lua',
        )

    def test_get_lua_paths_throws_exception_if_folder_doesnt_exist(self):
        fs = TempFS()

        map_file_repository = MapFileRepository(
            data_fs=fs,
        )

        self.assertRaises(
            ExceptionMapFolderNotFound,
            map_file_repository.get_lua_paths,
            1
        )
