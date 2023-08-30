from unittest import TestCase
from django.conf import os
from django.core.files.uploadedfile import SimpleUploadedFile
from fs.tempfs import TempFS
from openra.classes.screenshot_resource import ScreenshotResource
from openra.services.screenshot_repository import ExceptionInvalidMimeType, ScreenshotRepository

from openra.tests.factories import MapsFactory, UserFactory


class TestServiceScreenshotRepository(TestCase):

    def __get_uploaded_image_file(self):
        with open('openra/static/images/soviet-logo-fallback.png', 'rb') as file:
            data = file.read()
        return SimpleUploadedFile(
            'image.jpg',
            data,
            content_type='image/png'
        )

    def test_it_can_import_an_uploaded_file(self):
        user = UserFactory()
        map = MapsFactory()

        fs = TempFS()

        resource = ScreenshotResource('maps', map.id)

        file = self.__get_uploaded_image_file()

        repo = ScreenshotRepository(data_fs=fs)

        screenshot = repo.create_from_uploaded_file(
            file,
            user,
            resource,
            False
        )

        self.assertEquals(
            resource.id,
            screenshot.ex_id
        )

        self.assertEquals(
            resource.type,
            screenshot.ex_name
        )

        self.assertTrue(
            fs.exists(os.path.join('screenshots', str(screenshot.id), str(map.id) + '.png'))
        )

        self.assertTrue(
            fs.exists(os.path.join('screenshots', str(screenshot.id), str(map.id) + '-mini.png'))
        )

    def test_it_will_throw_an_invalid_mime_type_exception_when_not_an_image(self):
        user = UserFactory()
        map = MapsFactory()

        resource = ScreenshotResource('maps', map.id)

        file = SimpleUploadedFile('image.jpg', b'content')

        repo = ScreenshotRepository()

        self.assertRaises(
            ExceptionInvalidMimeType,
            repo.create_from_uploaded_file,
            file,
            user,
            resource,
            False
        )
