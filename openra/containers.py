from dependency_injector import containers, providers
from fs.osfs import OSFS
from openra import settings
from os import path
import docker
from openra.services.docker import Docker
from github import Github as GithubClient
from openra.services.github import Github

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

    github = providers.Singleton(
        Github,
        providers.Callable(
            GithubClient,
            settings.GITHUB_API_KEY
        )
    )
