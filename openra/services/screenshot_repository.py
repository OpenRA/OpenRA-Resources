import io
from dependency_injector.wiring import Provide, inject
from django.conf import os
from django.contrib.auth.models import User
from django.core.files.uploadedfile import UploadedFile
from django.utils import timezone
from fs.base import FS, copy
from openra.classes.exceptions import ExceptionBase
from openra.classes.file_location import FileLocation
from openra.classes.screenshot_resource import ScreenshotResource
from openra.models import Screenshots
from PIL import Image

from openra.services.uploaded_file_importer import UploadedFileImporter


class ScreenshotRepository:

    _data_fs: FS
    _uploaded_file_importer: UploadedFileImporter

    @inject
    def __init__(
        self,
        data_fs: FS = Provide['data_fs'],
        uploaded_file_importer: UploadedFileImporter = Provide['uploaded_file_importer']
    ):
        self._data_fs = data_fs
        self._uploaded_file_importer = uploaded_file_importer

    def create_from_uploaded_file(self, uploaded_file: UploadedFile, user: User, resource: ScreenshotResource, map_preview: bool):

        if uploaded_file.content_type not in ['image/jpeg', 'image/png', 'image/gif']:
            raise ExceptionInvalidMimeType(uploaded_file.name, uploaded_file.content_type)

        extension = uploaded_file.content_type.split('/')[1]

        uploaded = self._uploaded_file_importer.import_file(
            uploaded_file,
            uploaded_file.name
        )

        image = Image.open(
            uploaded.get_file_clone()
        )

        image.thumbnail((
            250,
            250
        ))

        thumbnail = io.BytesIO()

        image.save(thumbnail, extension)

        thumbnail.seek(0)

        model = Screenshots(
            user=user,
            ex_id=resource.id,
            ex_name=resource.type,
            posted=timezone.now(),
            map_preview=map_preview,
        )

        model.save()

        directory = os.path.join('screenshots', str(model.id))

        uploaded.copy_to_file_location(
            FileLocation(
                self._data_fs,
                directory,
                str(resource.id) + '.' + extension
            )
        )

        preview_path = os.path.join('screenshots', str(model.id), str(resource.id) + '-mini.' + extension)

        self._data_fs.writefile(
            preview_path,
            thumbnail
        )

        return model


class ExceptionInvalidMimeType(ExceptionBase):
    def __init__(self, filename: str, mimetype):
        super().__init__()
        self.message = "Mimetype invalid for a screenshot"
        self.detail.append('Filename : ' + filename)
        self.detail.append('Mimetype: ' + str(mimetype))
