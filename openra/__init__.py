from .containers import Container
from . import settings

container = Container()
container.config.from_dict(settings.__dict__)

default_app_config = 'openra.apps.OpenraConfig'
