from dependency_injector.wiring import providers
from openra import container


def register():
    container.log.override(providers.Singleton(
        FakeLog
    ))

entries = []

def contains(log_type, message):
    global entries
    for entry in entries:
        if entry['log_type'] == log_type and entry['message'] == message:
            return True
    return False

def clear():
    global entries
    entries = []

class FakeLog:


    def info(self, message:str):
        self._add_log('info', message)

    def warning(self, message:str):
        self._add_log('warning', message)

    def error(self, message:str):
        self._add_log('error', message)

    def _add_log(self, log_type, message):
        entries.append({
            'log_type':log_type,
            'message':message
        })