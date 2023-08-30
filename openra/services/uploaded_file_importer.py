from django.core.files.uploadedfile import File
from fs.tempfs import TempFS

from openra.classes.exceptions import ExceptionBase
from openra.classes.file_location import FileLocation


class UploadedFileImporter:

    def import_file(self, request_file: File, filename: str):

        try:
            temp_fs = self._create_temp_fs()

            for chunk in request_file.chunks():
                temp_fs.appendbytes(
                    filename,
                    chunk
                )

            return FileLocation(
                temp_fs,
                '',
                filename
            )
        except Exception as exception:
            raise ExceptionUploadedFileImporter(exception, filename)

    def _create_temp_fs(self):
        return TempFS()


class ExceptionUploadedFileImporter(ExceptionBase):
    def __init__(self, exception, filename: str):
        super().__init__()
        self.message = "Uploaded file importer caught an exception while attempting to upload this file"
        self.detail.append('filename: ' + filename)
        self.detail.append('message: ' + str(exception))
