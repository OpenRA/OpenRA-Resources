

from django.utils.timezone import datetime


class Log:

    def info(self, message:str):
        self._add_log('info', message)

    def warning(self, message:str):
        self._add_log('warning', message)

    def error(self, message:str):
        self._add_log('error', message)

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

