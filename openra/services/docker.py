import docker

from os import path
from django.conf import settings
import re
from docker.client import DockerClient


class Docker:

    _client: DockerClient

    def __init__(self, client:DockerClient):
        self._client = client

    def test_docker(self):
        return self._docker_run(
            'echo "Docker appears to be running ok"',
        )

    def extract_app_image(self, app_image_path, to_dir):
        pattern = re.compile('^[A-z0-9\-\/\.]+$')
        if not pattern.match(app_image_path):
            raise IncompatibleAppImagePathException('Incompatible character used in appimage path: ' + app_image_path)

        return self._docker_run(
            'bash -c "cp /in/AppImage . && '
                    './AppImage --appimage-extract && '
                    'rm AppImage"',
            volumes=[
                app_image_path+':/in/AppImage',
                to_dir+':/out/squashfs-root'
            ],
            working_dir='/out',
        )

    def run_utility_command(self, engine_path, command, additional_volumes=[]):
        return self._docker_run(
            '/engine/AppRun --utility ' + command,
            volumes=[
                engine_path+':/engine',
            ]+additional_volumes,
            working_dir='/build',
        )

    def _get_client(self):
        return self._client

    def _docker_run(self, command, volumes=[], working_dir='/'):
        client = self._get_client()

        return client.containers.run(
            self._get_docker_image(client),
            command,
            remove=True,
            volumes=volumes,
            working_dir=working_dir
        ).decode('UTF-8')


    def _get_docker_image(self, client):
        image_path = path.join(settings.BASE_DIR, 'openra', 'resources', 'docker')

        try:
            return client.images.get(settings.DOCKER_IMAGE_TAG)
        except:
            return client.images.build(path=image_path, tag=settings.DOCKER_IMAGE_TAG)[0]

class IncompatibleAppImagePathException(Exception):
    'Docker library only accepts basic characters, rename before extracting'
    pass
