
from openra.classes.exceptions import ExceptionBase


class ScreenshotResource:

    type: str
    id: int

    def __init__(self, type: str, id: int):
        if type not in ['maps']:
            raise ExceptionScreenshotResourceTypeInvalid(type, id)

        self.type = type
        self.id = id


class ExceptionScreenshotResourceTypeInvalid(ExceptionBase):
    def __init__(self, type: str, id: int):
        super().__init__()
        self.message = "Invalid resource type for screenshot resource"
        self.detail.append('Type : ' + type)
        self.detail.append('Id: ' + str(id))
