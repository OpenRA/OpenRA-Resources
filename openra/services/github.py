from datetime import date, datetime
from typing import List, Type
from dependency_injector.wiring import Provide, inject
from github import Github as GithubClient
from result import Err, Ok
from openra import settings
from openra.errors import ErrorBase

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

            return Ok(releases)
        except Exception as exception:
            return Err(ErrorGithubReleaseException(exception))



    def get_release_assets(self, tag):
        try:
            assets:List[GithubReleaseAsset] = []

            for asset in self._get_repo().get_release(tag).get_assets():
                assets.append(GithubReleaseAsset(
                    asset.name,
                    asset.browser_download_url
                ))

            return Ok(assets)
        except Exception as exception:
            return Err(ErrorGithubReleaseAssetsException(exception, tag))

    def _get_repo(self):
        if self._repo == None:
            self._repo = self._client.get_repo(settings.GITHUB_OPENRA_REPO, lazy=True)

        return self._repo

class GithubRelease:

    tag:str
    published:Type[datetime]

    def __init__(self, tag:str, published:Type[datetime]):
        self.tag = tag
        self.published = published

class GithubReleaseAsset:

    name:str
    url:str

    def __init__(self, name:str, url:str):
        self.name = name
        self.url = url


class ErrorGithubReleaseException(ErrorBase):
    def __init__(self, exception):
        super().__init__()
        self.message = "Github threw an exception while looking up available releases"
        self.detail.append('message: ' + str(exception))

class ErrorGithubReleaseAssetsException(ErrorBase):
    def __init__(self, exception, release:str):
        super().__init__()
        self.message = "Github threw an exception while looking up assets for a release"
        self.detail.append('release: ' + release)
        self.detail.append('message: ' + str(exception))
