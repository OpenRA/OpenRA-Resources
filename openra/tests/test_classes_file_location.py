import datetime
from fs.memoryfs import MemoryFS

from fs.tempfs import TempFS

from unittest import TestCase

from openra.classes.file_location import ErrorFileLocationCopyToTempFS, ErrorFileLocationGetOSDir, ErrorFileLocationGetOSPath, FileLocation

class TestFileLocation(TestCase):
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
            file.get_os_dir().unwrap()
        )

        self.assertFalse(
            'test_file'
            in
            file.get_os_dir().unwrap()
        )

    def test_dir_will_return_an_error_if_there_is_no_file_path(self):
        fs = MemoryFS()

        fs.makedir('location')
        fs.touch('location/test_file')

        file = FileLocation(
            fs,
            '/location/',
            'test_flie'
        )

        result = file.get_os_dir()

        self.assertIsInstance(
            result.unwrap_err(),
            ErrorFileLocationGetOSDir
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
            file.get_os_path().unwrap()
        )

    def test_file_will_return_an_error_if_there_is_no_file_path(self):
        fs = MemoryFS()

        fs.makedir('location')
        fs.touch('location/test_file')

        file = FileLocation(
            fs,
            '/location/',
            'test_flie'
        )

        result = file.get_os_path()

        self.assertIsInstance(
            result.unwrap_err(),
            ErrorFileLocationGetOSPath
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

        new_file = file.copy_to_tempfs('new_name').unwrap()

        self.assertEquals(
            'new_name',
             new_file.file
        )

        self.assertEquals(
            'file_content',
            new_file.fs.readtext('new_name')
        )

    def test_it_will_return_an_error_if_it_cant_copy_a_file_to_a_tempfs(self):
        fs = MemoryFS()

        fs.makedir('location')

        file = FileLocation(
            fs,
            'location/',
            'test_file'
        )

        self.assertIsInstance(
            file.copy_to_tempfs('new_name').unwrap_err(),
            ErrorFileLocationCopyToTempFS
        )
