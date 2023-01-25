

from openra.classes.exceptions import ExceptionBase


class ExceptionUtilityMapHashUnableToTranslate(ExceptionBase):
    def __init__(self, output: str):
        super().__init__()
        self.message = "Unable to translate response to map hash command"
        self.detail.append('command output: ' + output)
