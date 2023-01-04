import datetime

from django.utils import timezone
from unittest import TestCase
from unittest.mock import  Mock, MagicMock
from openra.services.docker import Docker, IncompatibleAppImagePathException
from os import path
from django.conf import settings

class TestServiceDocker(TestCase):

    def test_test_docker_will_pass_the_correct_parameters(self):
        clientMock = Mock()
        clientMock.containers = Mock()
        clientMock.images = Mock()
        clientMock.images.get = MagicMock(
            return_value ='fake_image'
        )
        clientMock.containers.run = MagicMock(
            return_value = b'mock_return'
        )

        docker = Docker()

        docker._getClient = MagicMock(
            return_value = clientMock
        )

        self.assertEquals(
            'mock_return',
            docker.testDocker()
        )

        clientMock.images.get.assert_called_once_with(settings.DOCKER_IMAGE_TAG)
        clientMock.containers.run.assert_called_once_with(
            'fake_image',
            'echo "Docker appears to be running ok"',
            remove=True,
            volumes=[],
            working_dir='/',
        )

    def test_extract_app_image_will_pass_the_correct_parameters(self):

        clientMock = Mock()
        clientMock.containers = Mock()
        clientMock.images = Mock()
        clientMock.images.get = MagicMock(
            return_value ='fake_image'
        )
        clientMock.containers.run = MagicMock(
            return_value = b'mock_return'
        )

        docker = Docker()

        docker._getClient = MagicMock(
            return_value = clientMock
        )

        self.assertEquals(
            'mock_return',
            docker.extractAppImage(
                '/sample/image.AppImage',
                '/extract/to/location',
            )
        )

        clientMock.images.get.assert_called_once_with(settings.DOCKER_IMAGE_TAG)

        clientMock.containers.run.assert_called_once_with(
            'fake_image',
            'bash -c "cp /in/AppImage . && '
                    './AppImage --appimage-extract && '
                    'rm AppImage"',
            remove=True,
            volumes=[
                '/sample/image.AppImage:/in/AppImage',
                '/extract/to/location:/out/squashfs-root'
            ],
            working_dir="/out",
        )

    def test_extract_app_image_will_throw_exception_if_an_incompatible_filename_is_used(self):
        clientMock = Mock()

        docker = Docker()

        docker._getClient = MagicMock(
            return_value = clientMock
        )

        self.assertRaises(
            IncompatibleAppImagePathException,
            docker.extractAppImage,
            '/sample/im age.AppImage',
            '/extract/to/location'
        )

    def test_run_utility_command_will_pass_the_correct_parameters(self):

        clientMock = Mock()
        clientMock.containers = Mock()
        clientMock.images = Mock()
        clientMock.images.get = MagicMock(
            side_effect = Exception()
        )
        clientMock.images.build = MagicMock(
            return_value=('fake_image', 'something_else')
        )
        clientMock.containers.run = MagicMock(
            return_value=b'mock_return'
        )

        docker = Docker()

        docker._getClient = MagicMock(
            return_value = clientMock
        )

        self.assertEquals(
            'mock_return',
            docker.runUtilityCommand(
                '/engine/path',
                'sample_command',
                [
                    'src/icons:icons'
                ]
            )
        )

        clientMock.images.get.assert_called_once_with(settings.DOCKER_IMAGE_TAG)

        imagePath = path.join(settings.BASE_DIR, 'openra', 'resources', 'docker')

        clientMock.images.build.assert_called_once_with(path=imagePath, tag=settings.DOCKER_IMAGE_TAG)

        clientMock.containers.run.assert_called_once_with(
            'fake_image',
            '/engine/AppRun --utility sample_command',
            remove=True,
            volumes=[
                '/engine/path:/engine',
                'src/icons:icons'
            ],
            working_dir="/build",
        )
