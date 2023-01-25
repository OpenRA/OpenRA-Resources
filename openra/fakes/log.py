from dependency_injector.wiring import providers
from openra.containers import container
from openra.classes.exceptions import ExceptionBase


class FakeLog:

    entries: list

    def __init__(self):
        self.entries = []

    def contains(self, log_type, message):
        for entry in self.entries:
            if entry['log_type'] == log_type and entry['message'] == message:
                return True
        return False

    def contains_all(self, entries):
        for entry in entries:
            if not self.contains(entry[0], entry[1]):
                return False
        return True

    def clear(self):
        self.entries = []

    def info(self, message: str):
        self._add_log('info', message)

    def warning(self, message: str):
        self._add_log('warning', message)

    def error(self, message: str):
        self._add_log('error', message)

    def exception_obj(self, exception: ExceptionBase):
        self._add_log('exception', exception.get_full_details())

    def _add_log(self, log_type, message):
        self.entries.append({
            'log_type': log_type,
            'message': message
        })
