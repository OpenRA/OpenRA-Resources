from unittest import TestCase
from unittest.mock import  Mock, MagicMock

from openra.services.docker import Docker, ExceptionDockerExceptionResponse, ExceptionDockerIncompatibleAppImagePath, ExceptionDockerNonByteResponse
from os import path
from django.conf import settings

class TestServiceDocker(TestCase):
    def test_that_test_docker_calls_lib_correctly_and_returns_output(self):
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

    def test_extract_appimage_calls_lib_correctly_and_returns_output(self):
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
                    'chmod +x AppImage && '
                    './AppImage --appimage-extract && '
                    'rm AppImage"',
            remove=True,
            volumes=[
                '/sample/image.AppImage:/in/AppImage',
                '/extract/to/location:/out/squashfs-root'
            ],
            working_dir="/out",
        )

    def test_extract_appimage_allows_acceptable_filenames(self):
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
                '/tmp/tmpkuld_787__tempfs__/appImage',
                '/extract/to/location',
            )
        )

    def test_extract_appimage_throws_exception_when_incompatible_filename_provided(self):
        client_mock = Mock()

        docker = Docker(client_mock)

        self.assertRaises(
            ExceptionDockerIncompatibleAppImagePath,
            docker.extract_appimage,
            '/sample/im age.App_image',
            '/extract/to/location'
        )

    def test_it_throws_exception_when_output_from_lib_is_non_byte(self):
        client_mock = Mock()
        client_mock.containers = Mock()
        client_mock.images = Mock()
        client_mock.images.get = MagicMock(
            return_value ='fake_image'
        )
        client_mock.containers.run = MagicMock(
            return_value = 'non byte response'
        )

        docker = Docker(client_mock)

        self.assertRaises(
            ExceptionDockerNonByteResponse,
            docker.test_docker
        )

    def test_it_throws_exception_when_client_containers_run_throws_exception(self):
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

        self.assertRaises(
            ExceptionDockerExceptionResponse,
            docker.test_docker
        )

    def test_run_utility_command_calls_lib_correctly_and_returns_output(self):
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
