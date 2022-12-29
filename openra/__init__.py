from .containers import ServiceContainer
from . import settings

container = ServiceContainer()
container.config.from_dict(settings.__dict__)
