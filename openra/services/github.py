from dependency_injector.wiring import Provide, inject
from github import Github as GithubClient
from openra import settings

class Github():

    _client: GithubClient
    _repo = None

    def __init__(self, client:GithubClient):
        self._client = client

    def list_releases(self):
        releases = []

        for release in self._get_repo().get_releases():
            releases.append({
                "tag": release.tag_name,
                "published": release.published_at,
            })

        return releases

    def get_release_assets(self, tag):
        assets = []

        for asset in self._get_repo().get_release(tag).get_assets():
            assets.append({
                "name": asset.name,
                "url": asset.browser_download_url,
            })

        return assets

    def _get_repo(self):
        if self._repo == None:
            self._repo = self._client.get_repo(settings.GITHUB_OPENRA_REPO, lazy=True)

        return self._repo

