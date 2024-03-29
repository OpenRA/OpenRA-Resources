from os import path
from django.conf import settings
import re
from docker.client import DockerClient

from openra.classes.exceptions import ExceptionBase


class Docker:

    _client: DockerClient

    def __init__(self, client: DockerClient):
        self._client = client

    def test_docker(self):
        return self._docker_run(
            'echo "Docker appears to be running ok"',
        )

    def extract_appimage(self, app_image_path: str, to_dir: str):
        pattern = re.compile('^[A-z0-9\-\/\.\_]+$')
        if not pattern.match(app_image_path):
            raise ExceptionDockerIncompatibleAppImagePath(app_image_path, to_dir)

        return self._docker_run(
            'bash -c "cp /in/AppImage . && '
            'chmod +x AppImage && '
            './AppImage --appimage-extract && '
            'rm AppImage"',
            volumes=[
                app_image_path + ':/in/AppImage',
                to_dir + ':/out/squashfs-root'
            ],
            working_dir='/out',
        )

    def run_utility_command(self, engine_path, command, additional_volumes=[]):
        output = self._docker_run(
            '/engine/AppRun --utility ' + command,
            volumes=[
                engine_path + ':/engine',
            ] + additional_volumes,
            working_dir='/build',
        )

        return self._filter_utility_warning(output)

    def _filter_utility_warning(self, output: str):
        return re.sub('^WARNING: Unable to sync system certificate store - https requests will fail\n', '', output)

    def _docker_run(self, command: str, volumes: list = [], working_dir='/'):
        try:
            output = self._client.containers.run(
                self._get_docker_image(self._client),
                command,
                remove=True,
                volumes=volumes,
                working_dir=working_dir
            )
        except Exception as exception:
            raise ExceptionDockerExceptionResponse(exception, command, volumes, working_dir)
        if isinstance(output, bytes):
            return str(output.decode('UTF-8'))
        else:
            raise ExceptionDockerNonByteResponse(output, command, volumes, working_dir)

    def _get_docker_image(self, client):
        image_path = path.join(settings.BASE_DIR, 'openra', 'resources', 'docker')

        try:
            return client.images.get(settings.DOCKER_IMAGE_TAG)
        except BaseException:
            return client.images.build(path=image_path, tag=settings.DOCKER_IMAGE_TAG)[0]


class ExceptionDockerIncompatibleAppImagePath(ExceptionBase):
    def __init__(self, appimage_path, to_dir):
        super().__init__()
        self.message = "Incompatible AppImage path provided"
        self.detail.append('tip: rename the app image before passing in')
        self.detail.append('path: ' + appimage_path)
        self.detail.append('extracting to: ' + to_dir)


class ExceptionDockerNonByteResponse(ExceptionBase):

    def __init__(self, output, command: str, volumes: list, working_dir: str):
        super().__init__()
        self.message = "Docker non-byte response"
        self.detail.append('command: ' + command)
        if not volumes:
            self.detail.append('volumes: none')
        else:
            for volume in volumes:
                self.detail.append('volume: ' + volume)
        self.detail.append('working_dir: ' + working_dir)
        self.detail.append('output type: ' + str(type(output)))


class ExceptionDockerExceptionResponse(ExceptionBase):
    def __init__(self, exception, command: str, volumes: list, working_dir: str):
        super().__init__()
        self.message = "Docker threw an exception"
        self.detail.append('tip: most likely a non 0 response from the container')
        self.detail.append('command: ' + command)
        if not volumes:
            self.detail.append('volumes: none')
        else:
            for volume in volumes:
                self.detail.append('volume: ' + volume)
        self.detail.append('working_dir: ' + working_dir)
        self.detail.append('message: ' + str(exception))
