

from unittest import TestCase

from dependency_injector.wiring import Provide, inject
from fs.osfs import OSFS
from openra.services.engine_file_repository import EngineFileRepository
from openra.services.file_downloader import FileDownloader
from openra.services.github import Github

from openra.services.log import Log
from openra.services.map_file_repository import MapFileRepository
from openra.services.map_search import MapSearch
from openra.services.utility import Utility


class TestContainer(TestCase):

    @inject
    def test_log_singleton_can_be_injected(self,
                                           log: Log = Provide['log']):
        self.assertIsInstance(log, Log)

    @inject
    def test_data_fs_can_be_injected(self,
                                     data_fs: OSFS = Provide['data_fs']):
        self.assertIsInstance(data_fs, OSFS)

    @inject
    def test_github_can_be_injected(self,
                                    github: Github = Provide['github']):
        self.assertIsInstance(github, Github)

    @inject
    def test_engine_file_repository_can_be_injected(self,
                                                    engine_file_repository: EngineFileRepository = Provide['engine_file_repository']):
        self.assertIsInstance(engine_file_repository, EngineFileRepository)

    @inject
    def test_map_file_repository_can_be_injected(self,
                                                 map_file_repository: MapFileRepository = Provide['map_file_repository']):
        self.assertIsInstance(map_file_repository, MapFileRepository)

    @inject
    def test_file_downloader_can_be_injected(self,
                                             file_downloader: FileDownloader = Provide['file_downloader']):
        self.assertIsInstance(file_downloader, FileDownloader)

    @inject
    def test_utility_can_be_injected(self,
                                     utility: Utility = Provide['utility']):
        self.assertIsInstance(utility, Utility)

    @inject
    def test_map_search_can_be_injected(self,
                                        map_search: MapSearch = Provide['map_search']):
        self.assertIsInstance(map_search, MapSearch)
