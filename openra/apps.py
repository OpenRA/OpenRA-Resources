"""Application config module."""

from django.apps import AppConfig

from openra import container

class OpenraConfig(AppConfig):
    name = "openra"

    def ready(self):
        container.wire(modules=[
            ".handlers",
            ".tests.test_commands",
            ".management.commands.test_docker",
            ".management.commands.test_utility",
            ".management.commands.import_latest_engines",
            ".facades",
            '.services.engine_file_repository',
            '.services.map_file_repository'
        ])
