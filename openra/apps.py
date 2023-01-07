"""Application config module."""

from django.apps import AppConfig

from openra import container

class OpenraConfig(AppConfig):
    name = "openra"

    def ready(self):
        container.wire(modules=[
            ".handlers",
            ".tests.test_commands",
            ".management.commands.testdocker",
            ".management.commands.import_latest_engines",
            ".facades",
            '.services.engine_provider'
        ])
