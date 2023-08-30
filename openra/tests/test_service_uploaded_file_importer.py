from unittest import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from openra.services.uploaded_file_importer import ExceptionUploadedFileImporter, UploadedFileImporter


class TestUploadedFileImporter(TestCase):

    def test_it_can_import_an_uploaded_file(self):
        file = SimpleUploadedFile('image.jpg', b'content')

        importer = UploadedFileImporter()

        location = importer.import_file(file, 'imported.jpg')

        self.assertEquals(
            'content',
            location.fs.readtext(
                location.get_fs_path()
            )
        )

        self.assertEquals(
            'imported.jpg',
            location.get_fs_path()
        )

    def test_it_can_throw_an_exception_if_the_file_doesnt_exist(self):
        importer = UploadedFileImporter()

        self.assertRaises(
            ExceptionUploadedFileImporter,
            importer.import_file,
            'test_url',
            'file_name'
        )
