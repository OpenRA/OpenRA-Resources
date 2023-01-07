import datetime

from django.utils import timezone
from unittest import TestCase
from unittest.mock import  Mock, MagicMock

from docker.errors import ContainerError
from openra.services.docker import Docker, IncompatibleAppImagePathException
from openra.fakes import log
from os import path
from django.conf import settings

class TestServiceDocker(TestCase):

    def test_that_test_docker_will_pass_the_correct_parameters(self):
        client_mock = Mock()
        client_mock.containers = Mock()
        client_mock.images = Mock()
        client_mock.images.get = MagicMock(
            return_value ='fake_image'
        )
        client_mock.containers.run = MagicMock(
            return_value = b'mock_return'
        )

        docker = Docker(client_mock)

        self.assertEquals(
            'mock_return',
            docker.test_docker()
        )

        client_mock.images.get.assert_called_once_with(settings.DOCKER_IMAGE_TAG)
        client_mock.containers.run.assert_called_once_with(
            'fake_image',
            'echo "Docker appears to be running ok"',
            remove=True,
            volumes=[],
            working_dir='/',
        )

    def test_extract_appimage_will_pass_the_correct_parameters(self):
        client_mock = Mock()
        client_mock.containers = Mock()
        client_mock.images = Mock()
        client_mock.images.get = MagicMock(
            return_value ='fake_image'
        )
        client_mock.containers.run = MagicMock(
            return_value = b'mock_return'
        )

        docker = Docker(client_mock)

        self.assertEquals(
            'mock_return',
            docker.extract_appimage(
                '/sample/image.AppImage',
                '/extract/to/location',
            )
        )

        client_mock.images.get.assert_called_once_with(settings.DOCKER_IMAGE_TAG)

        client_mock.containers.run.assert_called_once_with(
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

    def test_extract_appimage_will_allow_acceptable_filenames(self):
        client_mock = Mock()

        docker = Docker(client_mock)

        client_mock.containers = Mock()
        client_mock.images = Mock()
        client_mock.images.get = MagicMock(
            return_value ='fake_image'
        )
        client_mock.containers.run = MagicMock(
            return_value = b'mock_return'
        )

        self.assertEquals(
            'mock_return',
            docker.extract_appimage(
                b'/tmp/tmpkuld_787__tempfs__/appImage',
                '/extract/to/location',
            )
        )

    def test_extract_appimage_will_throw_exception_if_an_incompatible_filename_is_used(self):
        client_mock = Mock()

        docker = Docker(client_mock)

        self.assertRaises(
            IncompatibleAppImagePathException,
            docker.extract_appimage,
            '/sample/im age.App_image',
            '/extract/to/location'
        )

    def test_run_utility_command_will_pass_the_correct_parameters(self):
        client_mock = Mock()
        client_mock.containers = Mock()
        client_mock.images = Mock()
        client_mock.images.get = MagicMock(
            side_effect = Exception()
        )
        client_mock.images.build = MagicMock(
            return_value=('fake_image', 'something_else')
        )
        client_mock.containers.run = MagicMock(
            return_value=b'mock_return'
        )

        docker = Docker(client_mock)

        self.assertEquals(
            'mock_return',
            docker.run_utility_command(
                '/engine/path',
                'sample_command',
                [
                    'src/icons:icons'
                ]
            )
        )

        client_mock.images.get.assert_called_once_with(settings.DOCKER_IMAGE_TAG)

        image_path = path.join(settings.BASE_DIR, 'openra', 'resources', 'docker')

        client_mock.images.build.assert_called_once_with(path=image_path, tag=settings.DOCKER_IMAGE_TAG)

        client_mock.containers.run.assert_called_once_with(
            'fake_image',
            '/engine/AppRun --utility sample_command',
            remove=True,
            volumes=[
                '/engine/path:/engine',
                'src/icons:icons'
            ],
            working_dir="/build",
        )

    def log_contains_non_bytes_message(self):
        return log.contains('info', 'Docker returned non bytes response')

    def test_that_it_will_log_an_entry_on_docker_run_if_docker_doesnt_return_bytes(self):
        log.register()

        client_mock = Mock()
        client_mock.containers = Mock()
        client_mock.images = Mock()
        client_mock.images.get = MagicMock(
            return_value ='fake_image'
        )
        client_mock.containers.run = MagicMock(
            return_value = None
        )

        docker = Docker(client_mock)

        self.assertFalse(self.log_contains_non_bytes_message())

        self.assertEquals(
            None,
            docker.test_docker()
        )

        self.assertTrue(self.log_contains_non_bytes_message())

        log.clear()

        self.assertFalse(self.log_contains_non_bytes_message())

        self.assertEquals(
            None,
            docker.extract_appimage('fake', 'fake')
        )

        self.assertTrue(self.log_contains_non_bytes_message())

        log.clear()

        self.assertFalse(self.log_contains_non_bytes_message())

        self.assertEquals(
            None,
            docker.run_utility_command('fake', 'fake', [])
        )

        self.assertTrue(self.log_contains_non_bytes_message())

    def log_contains_exception_message(self):
        return log.contains('info', 'Docker has thrown an exception, most likely non-0 return')

    def test_that_it_will_log_an_entry_on_docker_run_if_docker_throws_a_container_exception(self):
        log.register()

        client_mock = Mock()
        client_mock.containers = Mock()
        client_mock.images = Mock()
        client_mock.images.get = MagicMock(
            return_value ='fake_image'
        )
        client_mock.containers.run = MagicMock(
            side_effect = Exception()
        )

        docker = Docker(client_mock)

        self.assertFalse(self.log_contains_exception_message())

        self.assertEquals(
            None,
            docker.test_docker()
        )

        self.assertTrue(self.log_contains_exception_message())

        log.clear()

        self.assertFalse(self.log_contains_exception_message())

        self.assertEquals(
            None,
            docker.extract_appimage('fake', 'fake')
        )

        self.assertTrue(self.log_contains_exception_message())

        log.clear()

        self.assertFalse(self.log_contains_exception_message())

        self.assertEquals(
            None,
            docker.run_utility_command('fake', 'fake', [])
        )

        self.assertTrue(self.log_contains_exception_message())
