

from dependency_injector.wiring import Provide, inject

from openra.services.log import Log


@inject
def log(log: Log = Provide['log']):
    return log
