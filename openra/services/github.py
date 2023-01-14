from datetime import datetime
from typing import List, Type
from dependency_injector.wiring import Provide, inject
from github import Github as GithubClient
from openra import settings
from openra.classes.exceptions import ExceptionBase

class Github():

    _client: GithubClient
    _repo = None

    def __init__(self, client:GithubClient):
        self._client = client

    def get_releases(self):
        try:
            releases:List[GithubRelease] = []

            for release in self._get_repo().get_releases():
                releases.append(GithubRelease(
                    release.tag_name,
                    release.published_at,
                ))

            return releases
        except Exception as exception:
            raise ExceptionGithubReleaseException(exception)



    def get_release_assets(self, tag):
        try:
            assets:List[GithubReleaseAsset] = []

            for asset in self._get_repo().get_release(tag).get_assets():
                assets.append(GithubReleaseAsset(
                    asset.name,
                    asset.browser_download_url
                ))

            return assets
        except Exception as exception:
            raise ExceptionGithubReleaseAssetsException(exception, tag)

    def _get_repo(self):
        if self._repo == None:
            self._repo = self._client.get_repo(settings.GITHUB_OPENRA_REPO, lazy=True)

        return self._repo

class GithubRelease:

    tag:str
    published:datetime

    def __init__(self, tag:str, published:datetime):
        self.tag = tag
        self.published = published

class GithubReleaseAsset:

    name:str
    url:str

    def __init__(self, name:str, url:str):
        self.name = name
        self.url = url


class ExceptionGithubReleaseException(ExceptionBase):
    def __init__(self, exception):
        super().__init__()
        self.message = "Github threw an exception while looking up available releases"
        self.detail.append('message: ' + str(exception))

class ExceptionGithubReleaseAssetsException(ExceptionBase):
    def __init__(self, exception, release:str):
        super().__init__()
        self.message = "Github threw an exception while looking up assets for a release"
        self.detail.append('release: ' + release)
        self.detail.append('message: ' + str(exception))
