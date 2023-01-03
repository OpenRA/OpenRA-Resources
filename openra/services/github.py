from github import Github as GithubClient
from openra import settings

class Github():

    def listReleases(self):
        releases = []

        for release in self._getRepo().get_releases():
            releases.append({
                "tag":release.tag_name,
                "published":release.published_at,
            })

        return releases

    def getReleaseAssets(self, tag):
        assets = []

        for asset in self._getRepo().get_release(tag).get_assets():
            assets.append({
                "name":asset.name,
                "url":asset.browser_download_url,
            })

        return assets

    _repo = None

    def _getClient(self):
        return GithubClient(settings.GITHUB_API_KEY)

    def _getRepo(self):
        if self._repo == None:
            github = self._getClient()

            self._repo = github.get_repo(settings.GITHUB_OPENRA_REPO, lazy=True)

        return self._repo

