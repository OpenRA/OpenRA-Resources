from openra.facades import log
from typing import List
from dependency_injector.wiring import Provide, inject
from django.core.management.base import BaseCommand
from result import Err, Ok
from openra.containers import Container
import re
from openra.services.engine_provider import EngineProvider
from openra.services.file_downloader import FileDownloader

from openra.services.github import Github

class Command(BaseCommand):
    help = 'Pulls the latest engines from GitHub'

    def add_arguments(self, parser):
        parser.add_argument('release_count', type=int, nargs='?', default=1)
        pass

    def handle(self, *args, **options):
        release_count = options['release_count']
        log().info("Checking github for the last {} release(s)".format(release_count))
        engines_result = self._get_latest_engines(release_count)
        if isinstance(engines_result, Err):
            log().error_obj(engines_result.unwrap_err())
            return

        log().info('The following engines were discovered on github')
        for engine in engines_result.unwrap():
            log().info(engine.mod + ' ' + engine.version + ' ' + engine.url)

        download_result = self._download_engines(engines_result.unwrap())
        if isinstance(download_result, Err):
            log().error_obj(download_result.unwrap_err())
            return

        log().info('Complete')

    @inject
    def _get_latest_engines(self, release_count=1, github:Github=Provide[Container.github]):
        playtest_regex = re.compile('^playtest-')

        releases_result = github.get_releases()
        if isinstance(releases_result, Err):
            return releases_result

        engines:List[EngineInfo] = []
        release_added = False

        for release in releases_result.unwrap():
            tag = release.tag
            playtest = playtest_regex.match(tag)

            if playtest and release_added:
                continue

            engines_result = self._get_release_engines(tag, github)
            if isinstance(engines_result, Err):
                return engines_result

            engines += engines_result.unwrap()

            if playtest:
                continue

            release_count -= 1

            if release_count == 0:
                break
            else:
                release_added = True

        return Ok(engines)

    def _get_release_engines(self, tag, github:Github):
        assets_result = github.get_release_assets(
            tag
        )
        if isinstance(assets_result, Err):
            return assets_result

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

        engines:List[EngineInfo] = []

        for asset in assets_result.unwrap():
            for mod in mod_regex:
                if mod['regex'].match(asset.name):
                    engines.append(
                        EngineInfo(
                            mod['mod'],
                            tag,
                            asset.url
                        )
                    )

        return Ok(engines)

    @inject
    def _download_engines(self, engines,
            engine_provider:EngineProvider=Provide['engine_provider'],
            file_downloader:FileDownloader=Provide['file_downloader']
        ):
        for engine in engines:
            path_result = engine_provider.get_path(engine.mod, engine.version)
            if isinstance(path_result, Err):
                return path_result

            if path_result.unwrap() == None:
                log().info('Downloading: ' + engine.mod + ' ' + engine.version)
                appimage_download_result = file_downloader.download_file(engine.url, 'appImage')

                if isinstance(appimage_download_result, Err):
                    return appimage_download_result

                log().info('Importing: ' + engine.mod + ' ' + engine.version)
                import_result = engine_provider.import_appimage(engine.mod, engine.version, appimage_download_result.unwrap())

                if isinstance(import_result, Err):
                    return import_result
            else:
                log().info('Engine already exists: ' + engine.mod + ' ' + engine.version)
        return Ok()

class EngineInfo:

    mod:str
    version:str
    url:str

    def __init__(self, mod, version, url):
        self.mod = mod
        self.version = version
        self.url = url


