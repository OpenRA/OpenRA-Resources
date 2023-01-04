from dependency_injector import containers, providers
from fs.memoryfs import MemoryFS
from fs.osfs import OSFS
from openra import settings
from os import path

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    dataFs = providers.Singleton(
        OSFS,
        path.join(settings.BASE_DIR, 'openra', 'data')
    )
