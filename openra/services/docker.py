from typing import List, TypeVar

from os import path
from django.conf import settings
import re
from docker.client import DockerClient
from result import Ok, Err, Result

class Docker:

    _client: DockerClient

    def __init__(self, client:DockerClient):
        self._client = client

    def test_docker(self):
        return self._docker_run(
            'echo "Docker appears to be running ok"',
        )

    def extract_appimage(self, app_image_path:str, to_dir:str):
        pattern = re.compile('^[A-z0-9\-\/\.\_]+$')
        if not pattern.match(app_image_path):
            return Err(ErrorDockerIncompatibleAppImagePath(app_image_path, to_dir))

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

    def _docker_run(self, command:str, volumes:list=[], working_dir='/'):
        try:
            output = self._client.containers.run(
                self._get_docker_image(self._client),
                command,
                remove=True,
                volumes=volumes,
                working_dir=working_dir
            )
            if isinstance(output, bytes):
                return Ok(str(output.decode('UTF-8')))
            else:
                return Err(ErrorDockerNonByteResponse(output, command, volumes, working_dir))
        except Exception as exception:
            return Err(ErrorDockerExceptionResponse(exception, command, volumes, working_dir))



    def _get_docker_image(self, client):
        image_path = path.join(settings.BASE_DIR, 'openra', 'resources', 'docker')

        try:
            return client.images.get(settings.DOCKER_IMAGE_TAG)
        except:
            return client.images.build(path=image_path, tag=settings.DOCKER_IMAGE_TAG)[0]

class ErrorBase:

    message: str
    friendly: str
    detail: List[str]

    def __init__(self):
        self.message = ''
        self.detail = [] 
        self.friendly = 'An error occurred, please try again later'

    def get_full_details(self):
        buffer = 'User Message: ' + self.friendly
        buffer += '\n\n'
        buffer += 'Error: ' + self.message
        buffer += '\n\n'
        buffer += 'Additional Details:\n'
        for line in self.detail:
            buffer += line + '\n'
        return buffer

    def print_full_details(self):
        print(self.get_full_details())

class ErrorDockerIncompatibleAppImagePath(ErrorBase):
    def __init__(self, appimage_path, to_dir):
        super().__init__()
        self.message = "Incompatible AppImage path provided"
        self.detail.append('tip: rename the app image before passing in')
        self.detail.append('path: ' + appimage_path)
        self.detail.append('extracting to: ' + to_dir)

class ErrorDockerNonByteResponse(ErrorBase):

    def __init__(self, output, command:str, volumes:list, working_dir:str):
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

class ErrorDockerExceptionResponse(ErrorBase):
    def __init__(self, exception, command:str, volumes:list, working_dir:str):
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
