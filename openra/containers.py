from dependency_injector import containers, providers
from fs.osfs import OSFS
from openra import settings
from os import path
import docker

from openra.services.docker import Docker

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    data_fs = providers.Singleton(
        OSFS,
        path.join(settings.BASE_DIR, 'openra', 'data')
    )

    docker = providers.Singleton(
        Docker,
        providers.Callable(
            docker.from_env
        )
    )

