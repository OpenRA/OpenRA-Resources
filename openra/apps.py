"""Application config module."""

from django.apps import AppConfig

class OpenraConfig(AppConfig):
    name = "openra"

    def ready(self):
        # Import late as some services will need django assets
        from openra.containers import container

        container.wire(modules=[
            ".views",
            ".handlers",
            ".tests.test_commands",
            ".management.commands.test_docker",
            ".management.commands.test_utility",
            ".management.commands.import_latest_engines",
            ".facades",
            '.services.engine_file_repository',
            '.services.map_file_repository'
        ])
