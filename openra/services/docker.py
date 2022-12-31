import docker

from os import path
from django.conf import settings


class Docker:

    def testDocker(self):
        return self._dockerRun(
            'echo "Docker appears to be running ok"',
        )

    def extractAppImage(self, appImagePath, toDir):
        appImage = path.basename(appImagePath)
        return self._dockerRun(
            'bash -c "cp /in/{0} . && '
                    './{0} --appimage-extract && '
                    'rm {0}"'.format(appImage),
            volumes=[
                appImagePath+':/in/'+appImage,
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
            return client.images.get('rc-ubuntu')
        except:
            return client.images.build(path=imagePath, tag="rc-ubuntu")[0]


