import datetime
from fs.memoryfs import MemoryFS

from fs.tempfs import TempFS

from unittest import TestCase

from openra.classes.file_location import ExceptionFileLocationCopyToTempFS, ExceptionFileLocationGetFileClone, ExceptionFileLocationGetOSDir, ExceptionFileLocationGetOSPath, FileLocation


class TestFileLocation(TestCase):
    def test_get_os_dir_returns_dir(self):
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

    def test_get_os_dir_throws_exception_if_no_os_dir(self):
        fs = MemoryFS()

        fs.makedir('location')
        fs.touch('location/test_file')

        file = FileLocation(
            fs,
            '/location/',
            'test_flie'
        )

        self.assertRaises(
            ExceptionFileLocationGetOSDir,
            file.get_os_dir
        )

    def test_get_os_path_returns_path(self):
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

    def test_get_os_path_throws_exception_if_no_os_path(self):
        fs = MemoryFS()

        fs.makedir('location')
        fs.touch('location/test_file')

        file = FileLocation(
            fs,
            '/location/',
            'test_flie'
        )

        self.assertRaises(
            ExceptionFileLocationGetOSPath,
            file.get_os_path
        )

    def test_copy_to_file_location_copies_a_file(self):
        fs = MemoryFS()

        fs.makedir('location')
        fs.writetext('location/test_file', 'file_content')

        file = FileLocation(
            fs,
            'location/',
            'test_file'
        )

        fs2 = MemoryFS()

        file2 = FileLocation(
            fs2,
            'location2/',
            'test_file2'
        )

        file.copy_to_file_location(file2)

        self.assertEquals(
            'file_content',
            file2.fs.readtext(file2.get_fs_path())
        )

    def test_copy_to_tempfs_copies_a_file(self):
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

    def test_copy_to_tempfs_throws_exception_if_unable_to_copy(self):
        fs = MemoryFS()

        fs.makedir('location')

        file = FileLocation(
            fs,
            'location/',
            'test_file'
        )

        self.assertRaises(
            ExceptionFileLocationCopyToTempFS,
            file.copy_to_tempfs,
            'new_name'
        )

    def test_get_file_clone(self):
        fs = MemoryFS()

        fs.makedir('location')
        fs.writetext('location/test_file', 'file_content')

        file = FileLocation(
            fs,
            'location/',
            'test_file'
        )

        clone = file.get_file_clone()

        self.assertEquals(
            b'file_content',
            clone.read()
        )

    def test_get_file_clone_throws_exception_if_unable_to_clone(self):
        fs = MemoryFS()

        fs.makedir('location')

        file = FileLocation(
            fs,
            'location/',
            'test_file'
        )

        self.assertRaises(
            ExceptionFileLocationGetFileClone,
            file.get_file_clone
        )
