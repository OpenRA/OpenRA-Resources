from dependency_injector import containers, providers
from fs.memoryfs import MemoryFS
from fs.osfs import OSFS
from openra import settings
from os import path

class ServiceContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    fs = providers.Singleton(
        OSFS,
        path.join(settings.BASE_DIR, 'openra', 'data')
    )
