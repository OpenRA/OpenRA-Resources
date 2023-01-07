from dependency_injector.wiring import Provide, inject
from django.core.management.base import BaseCommand, CommandError
import github
from openra.containers import Container
import re
from openra.services.engine_provider import EngineProvider

from openra.services.github import Github

class Command(BaseCommand):
    help = 'Pulls the latest engines from GitHub'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        releases = self._get_latest_releases()

        self._download_releases(releases)

    @inject
    def _get_latest_releases(self, github:Github=Provide[Container.github]):
        playtest_regex = re.compile('^playtest-')

        releases = []

        for release in github.list_releases():
            tag = release['tag']
            releases.append({
                'release': tag,
                'engines': self._get_release_engines(tag, github)
            })
            if playtest_regex.match(tag):
                continue
            break

        return releases

    def _get_release_engines(self, tag, github):
        assets = github.get_release_assets(
            tag
        )

        mod_regex = [{
            'mod': 'ra',
            'regex': re.compile('^OpenRA-Red-Alert-.*\.AppImage$')
         },{
             'mod': 'td',
             'regex': re.compile('^OpenRA-Tiberian-Dawn-.*\.AppImage$')
         },{
             'mod': 'd2k',
             'regex': re.compile('^OpenRA-Dune-2000-.*\.AppImage$')
        }]

        engines = []

        for asset in assets:
            for mod in mod_regex:
                if mod['regex'].match(asset['name']):
                    engines.append({
                        'mod': mod['mod'],
                        'url': asset['url']
                    })

        return engines

    @inject
    def _download_releases(self, releases, engine_provider:EngineProvider=Provide['engine_provider']):
        for release in releases:
            for engine in release['engines']:
                if engine_provider.get_path(engine['mod'], release['release']) == None:
                    engine_provider.import_appimage_by_url(engine['mod'], release['release'], engine['url'])

