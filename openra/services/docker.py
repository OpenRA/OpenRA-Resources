import docker

from os import path
from django.conf import settings
import re


class Docker:

    def testDocker(self):
        return self._dockerRun(
            'echo "Docker appears to be running ok"',
        )

    def extractAppImage(self, appImagePath, toDir):
        pattern = re.compile("^[A-z0-9\-\/\.]+$")
        if not pattern.match(appImagePath):
            raise IncompatibleAppImagePathException('Incompatible character used in appimage path: ' + appImagePath)

        appImage = path.basename(appImagePath)
        return self._dockerRun(
            'bash -c "cp /in/AppImage . && '
                    './AppImage --appimage-extract && '
                    'rm AppImage"',
            volumes=[
                appImagePath+':/in/AppImage',
                toDir+':/out/squashfs-root'
            ],
            workingDir="/out",
        )

    def runUtilityCommand(self, enginePath, command, additionalVolumes=[]):
        return self._dockerRun(
            '/engine/AppRun --utility ' + command,
            volumes=[
                enginePath+':/engine',
            ]+additionalVolumes,
            workingDir="/build",
        )

    def _getClient(self):
        return docker.from_env()

    def _dockerRun(self, command, volumes=[], workingDir="/"):
        client = self._getClient()

        return client.containers.run(
            self._getDockerImage(client),
            command,
            remove=True,
            volumes=volumes,
            working_dir=workingDir
        ).decode('UTF-8')


    def _getDockerImage(self, client):
        imagePath = path.join(settings.BASE_DIR, 'openra', 'resources', 'docker')

        try:
            return client.images.get(settings.DOCKER_IMAGE_TAG)
        except:
            return client.images.build(path=imagePath, tag=settings.DOCKER_IMAGE_TAG)[0]

class IncompatibleAppImagePathException(Exception):
    "Docker library only accepts basic characters, rename before extracting"
    pass
