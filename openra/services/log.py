from django.utils.timezone import datetime

from openra.classes.exceptions import ExceptionBase


class Log:

    def info(self, message: str):
        self._add_log('info', message)

    def warning(self, message: str):
        self._add_log('warning', message)

    def error(self, message: str):
        self._add_log('error', message)

    def exception_obj(self, exception: ExceptionBase):
        self._add_log('exception', exception.get_full_details())

    def _add_log(self, log_type, message):
        print(
            "{} {}: {}".format(
                self._formatted_time(),
                log_type,
                message
            )
        )

    def _formatted_time(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
