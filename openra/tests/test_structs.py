import datetime
from fs.memoryfs import MemoryFS

from fs.tempfs import TempFS
from fs.base import errors

from unittest import TestCase
from openra.structs import FileLocation

class TestStructs(TestCase):
    def test_dir_location_can_return_an_os_path_if_available(self):
        fs = TempFS()

        fs.makedir('location')
        fs.touch('location/test_file')

        file = FileLocation(
            fs,
            '/location/',
            'test_file'
        )

        self.assertTrue(
            '/location/'
            in
            file.get_os_dir()
        )

        self.assertFalse(
            'test_file'
            in
            file.get_os_dir()
        )

    def test_dir_will_throw_an_exception_if_there_is_no_file_path(self):
        fs = MemoryFS()

        fs.makedir('location')
        fs.touch('location/test_file')

        file = FileLocation(
            fs,
            '/location/',
            'test_flie'
        )

        self.assertRaises(
            errors.NoSysPath,
            file.get_os_dir
        )

    def test_file_location_can_return_an_os_path_if_available(self):
        fs = TempFS()

        fs.makedir('location')
        fs.touch('location/test_file')

        file = FileLocation(
            fs,
            '/location/',
            'test_file'
        )

        self.assertTrue(
            '/location/test_file'
            in
            file.get_os_path()
        )

    def test_file_will_throw_an_exception_if_there_is_no_file_path(self):
        fs = MemoryFS()

        fs.makedir('location')
        fs.touch('location/test_file')

        file = FileLocation(
            fs,
            '/location/',
            'test_flie'
        )

        self.assertRaises(
            errors.NoSysPath,
            file.get_os_path
        )

    def test_it_can_copy_a_file_to_a_tempfs(self):
        fs = MemoryFS()

        fs.makedir('location')
        fs.writetext('location/test_file', 'file_content')

        file = FileLocation(
            fs,
            'location/',
            'test_file'
        )

        new_file = file.copy_to_tempfs('new_name')

        self.assertEquals(
            'new_name',
             new_file.file
        )

        self.assertEquals(
            'file_content',
            new_file.fs.readtext('new_name')
        )



