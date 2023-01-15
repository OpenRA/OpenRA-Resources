from dependency_injector import containers, providers
from fs.osfs import OSFS
from openra import settings
from os import path
import docker
from openra.services.docker import Docker
from github import Github as GithubClient
from openra.services.engine_file_repository import EngineFileRepository
from openra.services.file_downloader import FileDownloader
from openra.services.github import Github
from openra.services.log import Log
from openra.services.map_file_repository import MapFileRepository
from openra.services.utility import Utility

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    log = providers.Singleton(
        Log
    )

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

    engine_file_repository = providers.Singleton(
        EngineFileRepository
    )

    map_file_repository = providers.Singleton(
        MapFileRepository
    )

    file_downloader = providers.Singleton(
        FileDownloader
    )

    utility = providers.Singleton(
        Utility
    )
