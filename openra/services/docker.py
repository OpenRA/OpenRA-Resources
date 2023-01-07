from django.core.management import os
import docker

from os import path
from django.conf import settings
import re
from docker.client import DockerClient
from docker.errors import ContainerError

from openra.facades import log


class Docker:

    _client: DockerClient

    def __init__(self, client:DockerClient):
        self._client = client

    def test_docker(self):
        return self._docker_run(
            'echo "Docker appears to be running ok"',
        )

    def extract_appimage(self, app_image_path, to_dir):
        pattern = re.compile('^[A-z0-9\-\/\.\_]+$')
        if not pattern.match(app_image_path):
            raise IncompatibleAppImagePathException('Incompatible character used in appimage path: ' + app_image_path)

        print('below')
        print(app_image_path+':/in/AppImage')
        print(to_dir+':/out/squashfs-root')
        print(os.path.isdir(app_image_path))
        print(os.path.exists(app_image_path))
        return self._docker_run(
            'bash -c "cp /in/AppImage . && '
                    'chmod +x AppImage && '
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

    def _docker_run(self, command, volumes=[], working_dir='/'):
        # try:
            output = self._client.containers.run(
                self._get_docker_image(self._client),
                command,
                remove=True,
                volumes=volumes,
                working_dir=working_dir
            )
            if isinstance(output, bytes):
                return str(output.decode('UTF-8'))
            else:
                log().info('Docker returned non bytes response')
        # except:
        #     log().info('Docker has thrown an exception, most likely non-0 return')

        # return None


    def _get_docker_image(self, client):
        image_path = path.join(settings.BASE_DIR, 'openra', 'resources', 'docker')

        try:
            return client.images.get(settings.DOCKER_IMAGE_TAG)
        except:
            return client.images.build(path=image_path, tag=settings.DOCKER_IMAGE_TAG)[0]

class IncompatibleAppImagePathException(Exception):
    'Docker library only accepts basic characters, rename before extracting'
    pass
